"""Reproducible inference runner.

This module provides a CLI and API for running the TF-IDF baseline
matcher with full reproducibility metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from nomenclador_conceptos_luis.data import load_icd10, load_icd11
from nomenclador_conceptos_luis.modeling import MatchConfig, compute_candidates, results_to_dataframe


def compute_file_hashes(paths: list[Path]) -> dict[str, str]:
    """Compute SHA-256 hashes for a list of files.

    Args:
        paths: List of file paths.

    Returns:
        Dictionary mapping filename to SHA-256 hash.
    """
    hashes: dict[str, str] = {}
    for path in paths:
        if path.exists():
            sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes[path.name] = sha256
    return hashes


def run_inference(
    icd10_path: Path | None = None,
    icd11_path: Path | None = None,
    output_dir: Path | None = None,
    top_k: int = 10,
    abstain_threshold: float = 0.01,
    skip_validation: bool = False,
) -> dict:
    """Run inference with full metadata.

    Args:
        icd10_path: Path to ICD-10 XML file.
        icd11_path: Path to ICD-11 TSV file.
        output_dir: Directory for output files.
        top_k: Number of top candidates to return.
        abstain_threshold: Threshold for abstention.
        skip_validation: If True, skip mapping validation.

    Returns:
        Dictionary with metadata and results.
    """
    # Default paths
    if icd10_path is None:
        icd10_path = Path("data/raw/icd10/icd102019en.xml")
    if icd11_path is None:
        icd11_path = Path("data/raw/icd11/SimpleTabulation-ICD-11-MMS-en.txt")
    if output_dir is None:
        output_dir = Path("data/processed")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Compute file hashes
    input_files = [icd10_path, icd11_path]
    if not skip_validation:
        mapping_path = Path("data/raw/mapping/mapping.zip")
        if mapping_path.exists():
            input_files.append(mapping_path)

    file_hashes = compute_file_hashes(input_files)

    # Load data
    print(f"Loading ICD-10 from {icd10_path}...")
    icd10_df = load_icd10(icd10_path)
    print(f"  Loaded {len(icd10_df)} ICD-10 records")

    print(f"Loading ICD-11 from {icd11_path}...")
    icd11_df = load_icd11(icd11_path)
    print(f"  Loaded {len(icd11_df)} ICD-11 records")

    # Run matching
    config = MatchConfig(top_k=top_k, abstain_threshold=abstain_threshold)
    print("Computing TF-IDF candidates...")
    output = compute_candidates(icd10_df, icd11_df, config)

    # Convert to DataFrame
    results_df = results_to_dataframe(output)

    # Save results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results_path = output_dir / f"predictions_{timestamp}.csv"
    results_df.to_csv(results_path, index=False)
    print(f"Saved predictions to {results_path}")

    # Save metadata
    metadata = {
        "timestamp": timestamp,
        "method": "tfidf_char_ngrams",
        "method_version": "1.0.0",
        "config": {
            "ngram_range": config.ngram_range,
            "top_k": config.top_k,
            "abstain_threshold": config.abstain_threshold,
            "max_features": config.max_features,
        },
        "input_files": {str(k): v for k, v in file_hashes.items()},
        "stats": {
            "source_count": output.source_count,
            "target_count": output.target_count,
            "total_predictions": len(output.results),
            "abstained_count": output.abstained_count,
        },
        "icd10_version": "2019",
        "icd11_version": "2026-01",
    }

    metadata_path = output_dir / f"metadata_{timestamp}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {metadata_path}")

    return metadata


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run TF-IDF baseline inference for ICD-10 to ICD-11 mapping"
    )
    parser.add_argument(
        "--icd10",
        type=Path,
        default=None,
        help="Path to ICD-10 XML file",
    )
    parser.add_argument(
        "--icd11",
        type=Path,
        default=None,
        help="Path to ICD-11 TSV file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top candidates (default: 10)",
    )
    parser.add_argument(
        "--abstain-threshold",
        type=float,
        default=0.01,
        help="Abstention threshold (default: 0.01)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip mapping validation",
    )

    args = parser.parse_args()

    metadata = run_inference(
        icd10_path=args.icd10,
        icd11_path=args.icd11,
        output_dir=args.output_dir,
        top_k=args.top_k,
        abstain_threshold=args.abstain_threshold,
        skip_validation=args.skip_validation,
    )

    print("\nInference complete!")
    print(f"  Source codes: {metadata['stats']['source_count']}")
    print(f"  Target codes: {metadata['stats']['target_count']}")
    print(f"  Predictions: {metadata['stats']['total_predictions']}")
    print(f"  Abstained: {metadata['stats']['abstained_count']}")


if __name__ == "__main__":
    main()
