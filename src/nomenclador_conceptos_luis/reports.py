"""Report generation and error analysis.

This module generates versioned reports with metrics, error analysis,
and reproduction instructions.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from nomenclador_conceptos_luis.evaluation import EvaluationMetrics, EvaluationDetail


def generate_report(
    metrics: EvaluationMetrics,
    details: list[EvaluationDetail],
    metadata: dict,
    output_dir: Path | None = None,
) -> Path:
    """Generate a comprehensive evaluation report.

    Args:
        metrics: Evaluation metrics.
        details: Per-source evaluation details.
        metadata: Inference metadata.
        output_dir: Output directory.

    Returns:
        Path to the generated report.
    """
    if output_dir is None:
        output_dir = Path("reports")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Generate markdown report
    report_lines = [
        "# ICD-10 to ICD-11 Mapping Evaluation Report",
        "",
        f"**Generated**: {timestamp}",
        f"**Method**: {metadata.get('method', 'unknown')}",
        f"**Method Version**: {metadata.get('method_version', 'unknown')}",
        "",
        "---",
        "",
        "## Configuration",
        "",
        f"- **N-gram range**: {metadata.get('config', {}).get('ngram_range', 'N/A')}",
        f"- **Top-k**: {metadata.get('config', {}).get('top_k', 'N/A')}",
        f"- **Abstain threshold**: {metadata.get('config', {}).get('abstain_threshold', 'N/A')}",
        "",
        "## Input Data",
        "",
        f"- **ICD-10 version**: {metadata.get('icd10_version', 'N/A')}",
        f"- **ICD-11 version**: {metadata.get('icd11_version', 'N/A')}",
        "",
        "### File Hashes (SHA-256)",
        "",
    ]

    for filename, hash_val in metadata.get("input_files", {}).items():
        report_lines.append(f"- **{filename}**: `{hash_val}`")

    report_lines.extend([
        "",
        "---",
        "",
        "## Results Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total source codes | {metrics.total_source} |",
        f"| Matched sources | {metrics.matched_source} |",
        f"| Coverage | {metrics.coverage:.1%} |",
        f"| Exact match (top-1) | {metrics.exact_match_top1:.1%} |",
        f"| Exact match (top-5) | {metrics.exact_match_top5:.1%} |",
        f"| Exact match (top-10) | {metrics.exact_match_top10:.1%} |",
        f"| Precision@1 | {metrics.precision_at1:.1%} |",
        f"| Recall@1 | {metrics.recall_at1:.1%} |",
        f"| Abstained | {metrics.abstained_count} ({metrics.abstained_pct:.1%}) |",
        f"| Missing in ground truth | {metrics.missing_in_gt} |",
        "",
        "---",
        "",
        "## Interpretation",
        "",
        "- **Probabilities are relative**, not clinically calibrated.",
        "- They indicate ranking confidence within the candidate list.",
        "- Do NOT interpret as diagnostic probabilities.",
        "",
        "---",
        "",
        "## Error Analysis",
        "",
    ])

    # Find worst predictions (not matched)
    not_matched = [d for d in details if not d.is_matched]
    if not_matched:
        report_lines.append("### Worst Predictions (not in ground truth)")
        report_lines.append("")
        report_lines.append("| Source | Title | Predicted | Ground Truth |")
        report_lines.append("|--------|-------|-----------|--------------|")
        for d in not_matched[:20]:
            pred_str = ", ".join(d.predicted[:3])
            gt_str = ", ".join(d.ground_truth[:3]) if d.ground_truth else "None"
            report_lines.append(
                f"| {d.source_code} | {d.source_title[:50]} | {pred_str} | {gt_str} |"
            )
        report_lines.append("")

    # Find abstained sources
    abstained = [d for d in details if not d.predicted]
    if abstained:
        report_lines.append("### Abstained Sources")
        report_lines.append("")
        report_lines.append(f"Total abstained: {len(abstained)}")
        report_lines.append("")

    # Find best predictions (matched with high score)
    matched = [d for d in details if d.is_matched and d.score_of_match is not None]
    if matched:
        matched_sorted = sorted(matched, key=lambda x: x.score_of_match or 0, reverse=True)
        report_lines.append("### Best Predictions (highest score)")
        report_lines.append("")
        report_lines.append("| Source | Title | Matched | Score | Rank |")
        report_lines.append("|--------|-------|---------|-------|------|")
        for d in matched_sorted[:10]:
            report_lines.append(
                f"| {d.source_code} | {d.source_title[:50]} | {d.ground_truth[0] if d.ground_truth else 'N/A'} | {d.score_of_match:.3f} | {d.rank_of_match} |"
            )
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## Reproduction",
        "",
        "To reproduce this evaluation:",
        "",
        "```bash",
        "# Install dependencies",
        "uv sync",
        "",
        "# Run inference",
        "python -m nomenclador_conceptos_luis.runner --top-k 10",
        "",
        "# Run evaluation",
        "python -m nomenclador_conceptos_luis.evaluation",
        "```",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "- Text-based matching only (no clinical semantics)",
        "- No hierarchical reasoning",
        "- Probabilities are relative, not calibrated",
        "- Ground truth may be incomplete",
        "",
        "## Future Improvements",
        "",
        "- Add hierarchical matching rules",
        "- Explore embeddings for semantic similarity",
        "- Consider record linkage techniques",
        "- Add clinical validation layer",
    ])

    # Write report
    report_path = output_dir / f"evaluation_report_{timestamp}.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    # Save metrics as JSON
    metrics_path = output_dir / f"metrics_{timestamp}.json"
    with open(metrics_path, "w") as f:
        json.dump(asdict(metrics), f, indent=2)

    # Save details as CSV
    details_df = pd.DataFrame([{
        "source_code": d.source_code,
        "source_title": d.source_title,
        "ground_truth": "|".join(d.ground_truth),
        "predicted": "|".join(d.predicted),
        "is_matched": d.is_matched,
        "rank_of_match": d.rank_of_match,
        "score_of_match": d.score_of_match,
    } for d in details])
    details_path = output_dir / f"details_{timestamp}.csv"
    details_df.to_csv(details_path, index=False)

    return report_path
