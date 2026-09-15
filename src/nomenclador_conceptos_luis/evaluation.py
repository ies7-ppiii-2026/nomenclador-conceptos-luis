"""Evaluation against official WHO mapping.

This module loads ground truth mapping files and computes metrics
to evaluate the quality of predictions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class EvaluationMetrics:
    """Evaluation metrics."""

    total_source: int
    matched_source: int
    coverage: float  # % of source codes with at least one prediction
    exact_match_top1: float  # % where top-1 prediction is in ground truth
    exact_match_top5: float  # % where at least one of top-5 is in ground truth
    exact_match_top10: float  # % where at least one of top-10 is in ground truth
    precision_at1: float
    recall_at1: float
    abstained_count: int
    abstained_pct: float
    missing_in_gt: int  # Source codes not in ground truth


@dataclass
class EvaluationDetail:
    """Detailed evaluation for a single source code."""

    source_code: str
    source_title: str
    ground_truth: list[str]
    predicted: list[str]
    is_matched: bool
    rank_of_match: int | None
    score_of_match: float | None


def load_ground_truth(mapping_dir: Path) -> pd.DataFrame:
    """Load official ground truth mapping.

    Reads both 10To11MapToOneCategory.txt and
    10To11MapToMultipleCategories.txt.

    Args:
        mapping_dir: Path to mapping directory.

    Returns:
        DataFrame with columns: source_code, target_code, source_title, target_title
    """
    dfs: list[pd.DataFrame] = []

    # Load single category mapping
    single_path = mapping_dir / "10To11MapToOneCategory.txt"
    if single_path.exists():
        df_single = pd.read_csv(single_path, sep="\t", dtype=str, keep_default_na=False)
        df_single = df_single.rename(columns={
            "icd10Code": "source_code",
            "icd11Code": "target_code",
            "icd10Title": "source_title",
            "icd11Title": "target_title",
        })
        dfs.append(df_single[["source_code", "target_code", "source_title", "target_title"]])

    # Load multiple category mapping
    multi_path = mapping_dir / "10To11MapToMultipleCategories.txt"
    if multi_path.exists():
        df_multi = pd.read_csv(multi_path, sep="\t", dtype=str, keep_default_na=False)
        df_multi = df_multi.rename(columns={
            "icd10Code": "source_code",
            "icd11Code": "target_code",
            "icd10Title": "source_title",
            "icd11Title": "target_title",
        })
        dfs.append(df_multi[["source_code", "target_code", "source_title", "target_title"]])

    if not dfs:
        raise FileNotFoundError(f"No mapping files found in {mapping_dir}")

    df = pd.concat(dfs, ignore_index=True)

    # Remove duplicates (same source-target pair)
    df = df.drop_duplicates(subset=["source_code", "target_code"])

    return df


def build_ground_truth_index(gt_df: pd.DataFrame) -> dict[str, set[str]]:
    """Build index from source code to set of target codes.

    Args:
        gt_df: Ground truth DataFrame.

    Returns:
        Dictionary mapping source code to set of target codes.
    """
    index: dict[str, set[str]] = {}
    for _, row in gt_df.iterrows():
        src = row["source_code"]
        tgt = row["target_code"]
        if src not in index:
            index[src] = set()
        index[src].add(tgt)
    return index


def evaluate_predictions(
    predictions_df: pd.DataFrame,
    gt_df: pd.DataFrame,
) -> tuple[EvaluationMetrics, list[EvaluationDetail]]:
    """Evaluate predictions against ground truth.

    Args:
        predictions_df: Predictions DataFrame with source_code, target_code, rank, score.
        gt_df: Ground truth DataFrame.

    Returns:
        Tuple of (metrics, details).
    """
    gt_index = build_ground_truth_index(gt_df)

    # Get unique source codes in predictions
    pred_sources = set(predictions_df["source_code"].unique())
    gt_sources = set(gt_index.keys())

    # Source codes not in ground truth
    missing_in_gt = len(pred_sources - gt_sources)

    # Evaluate each source code
    details: list[EvaluationDetail] = []
    matched_count = 0
    exact_top1 = 0
    exact_top5 = 0
    exact_top10 = 0
    precision_sum = 0.0
    recall_sum = 0.0
    abstained_count = 0

    for source_code in sorted(pred_sources):
        # Get predictions for this source
        preds = predictions_df[predictions_df["source_code"] == source_code]
        preds = preds.sort_values("rank")

        # Get ground truth targets
        gt_targets = gt_index.get(source_code, set())

        # Get predicted targets
        pred_targets = preds["target_code"].tolist()

        # Check if any prediction matches ground truth
        is_matched = False
        rank_of_match = None
        score_of_match = None

        for _, row in preds.iterrows():
            if row["target_code"] in gt_targets:
                is_matched = True
                rank_of_match = row["rank"]
                score_of_match = row["score"]
                break

        if is_matched:
            matched_count += 1

        # Check top-k
        top1_targets = set(pred_targets[:1])
        top5_targets = set(pred_targets[:5])
        top10_targets = set(pred_targets[:10])

        if top1_targets & gt_targets:
            exact_top1 += 1
        if top5_targets & gt_targets:
            exact_top5 += 1
        if top10_targets & gt_targets:
            exact_top10 += 1

        # Precision and recall at 1
        if top1_targets:
            precision_sum += len(top1_targets & gt_targets) / len(top1_targets)
        if gt_targets:
            recall_sum += len(top1_targets & gt_targets) / len(gt_targets)

        # Check abstention
        if preds["abstain"].any():
            abstained_count += 1

        # Get source title
        source_title = ""
        if not gt_df[gt_df["source_code"] == source_code].empty:
            source_title = gt_df[gt_df["source_code"] == source_code].iloc[0]["source_title"]

        details.append(
            EvaluationDetail(
                source_code=source_code,
                source_title=source_title,
                ground_truth=sorted(gt_targets),
                predicted=pred_targets[:10],
                is_matched=is_matched,
                rank_of_match=rank_of_match,
                score_of_match=score_of_match,
            )
        )

    total_source = len(pred_sources)
    coverage = matched_count / total_source if total_source > 0 else 0
    precision_at1 = precision_sum / total_source if total_source > 0 else 0
    recall_at1 = recall_sum / total_source if total_source > 0 else 0
    abstained_pct = abstained_count / total_source if total_source > 0 else 0

    metrics = EvaluationMetrics(
        total_source=total_source,
        matched_source=matched_count,
        coverage=coverage,
        exact_match_top1=exact_top1 / total_source if total_source > 0 else 0,
        exact_match_top5=exact_top5 / total_source if total_source > 0 else 0,
        exact_match_top10=exact_top10 / total_source if total_source > 0 else 0,
        precision_at1=precision_at1,
        recall_at1=recall_at1,
        abstained_count=abstained_count,
        abstained_pct=abstained_pct,
        missing_in_gt=missing_in_gt,
    )

    return metrics, details


def details_to_dataframe(details: list[EvaluationDetail]) -> pd.DataFrame:
    """Convert evaluation details to DataFrame.

    Args:
        details: List of EvaluationDetail.

    Returns:
        DataFrame with evaluation details.
    """
    rows = []
    for d in details:
        rows.append({
            "source_code": d.source_code,
            "source_title": d.source_title,
            "ground_truth": "|".join(d.ground_truth),
            "predicted": "|".join(d.predicted),
            "is_matched": d.is_matched,
            "rank_of_match": d.rank_of_match,
            "score_of_match": d.score_of_match,
        })
    return pd.DataFrame(rows)
