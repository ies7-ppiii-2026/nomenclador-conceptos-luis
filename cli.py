#!/usr/bin/env python3
"""CLI entry point for the nomenclador-conceptos-luis package.

Usage:
    python cli.py run          # Run inference
    python cli.py evaluate     # Run evaluation
    python cli.py pipeline     # Run full pipeline (inference + evaluation)
"""
from __future__ import annotations

import argparse
import sys


def cmd_run(args: argparse.Namespace) -> None:
    """Run inference."""
    from nomenclador_conceptos_luis.runner import run_inference

    run_inference(
        icd10_path=args.icd10,
        icd11_path=args.icd11,
        output_dir=args.output_dir,
        top_k=args.top_k,
        abstain_threshold=args.abstain_threshold,
        skip_validation=args.skip_validation,
    )


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Run evaluation."""
    from nomenclador_conceptos_luis.evaluation import run_evaluation

    run_evaluation(
        predictions_path=args.predictions,
        mapping_dir=args.mapping_dir,
        output_dir=args.output_dir,
    )


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Run full pipeline: inference + evaluation."""
    from nomenclador_conceptos_luis.runner import run_inference
    from nomenclador_conceptos_luis.evaluation import run_evaluation

    print("=" * 60)
    print("STEP 1: Running inference")
    print("=" * 60)
    run_inference(
        icd10_path=args.icd10,
        icd11_path=args.icd11,
        output_dir=args.output_dir,
        top_k=args.top_k,
        abstain_threshold=args.abstain_threshold,
        skip_validation=args.skip_validation,
    )

    print("\n" + "=" * 60)
    print("STEP 2: Running evaluation")
    print("=" * 60)
    run_evaluation(
        mapping_dir=args.mapping_dir,
        output_dir=args.output_dir,
    )

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ICD-10 to ICD-11 mapping toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run TF-IDF inference")
    run_parser.add_argument("--icd10", type=str, default=None, help="Path to ICD-10 XML")
    run_parser.add_argument("--icd11", type=str, default=None, help="Path to ICD-11 TSV")
    run_parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    run_parser.add_argument("--top-k", type=int, default=10, help="Top-k candidates")
    run_parser.add_argument("--abstain-threshold", type=float, default=0.01, help="Abstain threshold")
    run_parser.add_argument("--skip-validation", action="store_true", help="Skip mapping validation")
    run_parser.set_defaults(func=cmd_run)

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate predictions")
    eval_parser.add_argument("--predictions", type=str, default=None, help="Predictions CSV path")
    eval_parser.add_argument("--mapping-dir", type=str, default=None, help="Mapping directory")
    eval_parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    eval_parser.set_defaults(func=cmd_evaluate)

    # Pipeline command
    pipe_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipe_parser.add_argument("--icd10", type=str, default=None, help="Path to ICD-10 XML")
    pipe_parser.add_argument("--icd11", type=str, default=None, help="Path to ICD-11 TSV")
    pipe_parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    pipe_parser.add_argument("--top-k", type=int, default=10, help="Top-k candidates")
    pipe_parser.add_argument("--abstain-threshold", type=float, default=0.01, help="Abstain threshold")
    pipe_parser.add_argument("--skip-validation", action="store_true", help="Skip mapping validation")
    pipe_parser.add_argument("--mapping-dir", type=str, default=None, help="Mapping directory")
    pipe_parser.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
