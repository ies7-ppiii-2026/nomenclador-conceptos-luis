"""Tests for evaluation module."""
from pathlib import Path

import pandas as pd
import pytest

from nomenclador_conceptos_luis.evaluation import (
    EvaluationDetail,
    EvaluationMetrics,
    build_ground_truth_index,
    details_to_dataframe,
    evaluate_predictions,
    load_ground_truth,
)

RAW_DATA = Path("data/raw")


class TestLoadGroundTruth:
    """Tests for ground truth loading."""

    @pytest.mark.skipif(
        not (RAW_DATA / "mapping/10To11MapToOneCategory.txt").exists(),
        reason="Mapping data not available",
    )
    def test_loads_data(self) -> None:
        gt = load_ground_truth(RAW_DATA / "mapping")
        assert len(gt) > 0
        assert "source_code" in gt.columns
        assert "target_code" in gt.columns

    @pytest.mark.skipif(
        not (RAW_DATA / "mapping/10To11MapToOneCategory.txt").exists(),
        reason="Mapping data not available",
    )
    def test_no_duplicates(self) -> None:
        gt = load_ground_truth(RAW_DATA / "mapping")
        # Check no duplicate source-target pairs
        dupes = gt.duplicated(subset=["source_code", "target_code"])
        assert not dupes.any()


class TestBuildGroundTruthIndex:
    """Tests for ground truth index building."""

    def test_basic_index(self) -> None:
        gt_df = pd.DataFrame({
            "source_code": ["A00", "A00", "A01"],
            "target_code": ["1A00", "1A01", "1A02"],
            "source_title": ["Cholera", "Cholera", "Typhoid"],
            "target_title": ["Cholera", "Cholera", "Typhoid"],
        })
        index = build_ground_truth_index(gt_df)
        assert "A00" in index
        assert "A01" in index
        assert index["A00"] == {"1A00", "1A01"}
        assert index["A01"] == {"1A02"}


class TestEvaluatePredictions:
    """Tests for prediction evaluation."""

    def test_perfect_predictions(self) -> None:
        gt_df = pd.DataFrame({
            "source_code": ["A00", "A01"],
            "target_code": ["1A00", "1A02"],
            "source_title": ["Cholera", "Typhoid"],
            "target_title": ["Cholera", "Typhoid"],
        })
        pred_df = pd.DataFrame({
            "source_code": ["A00", "A01"],
            "target_code": ["1A00", "1A02"],
            "rank": [1, 1],
            "score": [0.9, 0.85],
            "probability": [1.0, 1.0],
            "abstain": [False, False],
        })
        metrics, details = evaluate_predictions(pred_df, gt_df)
        assert metrics.exact_match_top1 == 1.0
        assert metrics.coverage == 1.0

    def test_partial_predictions(self) -> None:
        gt_df = pd.DataFrame({
            "source_code": ["A00", "A01"],
            "target_code": ["1A00", "1A02"],
            "source_title": ["Cholera", "Typhoid"],
            "target_title": ["Cholera", "Typhoid"],
        })
        pred_df = pd.DataFrame({
            "source_code": ["A00", "A01"],
            "target_code": ["1A00", "1A99"],  # A01 wrong prediction
            "rank": [1, 1],
            "score": [0.9, 0.85],
            "probability": [1.0, 1.0],
            "abstain": [False, False],
        })
        metrics, details = evaluate_predictions(pred_df, gt_df)
        assert metrics.exact_match_top1 == 0.5  # Only A00 matches
        assert metrics.coverage == 0.5

    def test_abstained_predictions(self) -> None:
        gt_df = pd.DataFrame({
            "source_code": ["A00"],
            "target_code": ["1A00"],
            "source_title": ["Cholera"],
            "target_title": ["Cholera"],
        })
        pred_df = pd.DataFrame({
            "source_code": ["A00"],
            "target_code": ["1A00"],
            "rank": [1],
            "score": [0.005],  # Below threshold
            "probability": [1.0],
            "abstain": [True],
        })
        metrics, details = evaluate_predictions(pred_df, gt_df)
        assert metrics.abstained_count == 1
        assert metrics.abstained_pct == 1.0


class TestDetailsToDataframe:
    """Tests for details_to_dataframe."""

    def test_conversion(self) -> None:
        details = [
            EvaluationDetail(
                source_code="A00",
                source_title="Cholera",
                ground_truth=["1A00"],
                predicted=["1A00", "1A01"],
                is_matched=True,
                rank_of_match=1,
                score_of_match=0.9,
            )
        ]
        df = details_to_dataframe(details)
        assert len(df) == 1
        assert df.iloc[0]["source_code"] == "A00"
        assert df.iloc[0]["is_matched"] == True
