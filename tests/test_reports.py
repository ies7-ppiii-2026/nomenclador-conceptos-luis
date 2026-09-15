"""Tests for report generation."""
from pathlib import Path

import pytest

from nomenclador_conceptos_luis.evaluation import EvaluationMetrics, EvaluationDetail
from nomenclador_conceptos_luis.reports import generate_report


class TestGenerateReport:
    """Tests for report generation."""

    def test_generates_report(self, tmp_path: Path) -> None:
        metrics = EvaluationMetrics(
            total_source=100,
            matched_source=50,
            coverage=0.5,
            exact_match_top1=0.3,
            exact_match_top5=0.6,
            exact_match_top10=0.8,
            precision_at1=0.35,
            recall_at1=0.25,
            abstained_count=5,
            abstained_pct=0.05,
            missing_in_gt=10,
        )
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
        metadata = {
            "method": "tfidf_char_ngrams",
            "method_version": "1.0.0",
            "config": {"ngram_range": [2, 4], "top_k": 10, "abstain_threshold": 0.01},
            "input_files": {"test.txt": "abc123"},
            "icd10_version": "2019",
            "icd11_version": "2026-01",
        }

        report_path = generate_report(metrics, details, metadata, tmp_path)
        assert report_path.exists()
        assert report_path.suffix == ".md"

    def test_report_contains_metrics(self, tmp_path: Path) -> None:
        metrics = EvaluationMetrics(
            total_source=100,
            matched_source=50,
            coverage=0.5,
            exact_match_top1=0.3,
            exact_match_top5=0.6,
            exact_match_top10=0.8,
            precision_at1=0.35,
            recall_at1=0.25,
            abstained_count=5,
            abstained_pct=0.05,
            missing_in_gt=10,
        )
        details = []
        metadata = {
            "method": "tfidf_char_ngrams",
            "method_version": "1.0.0",
            "config": {"ngram_range": [2, 4], "top_k": 10, "abstain_threshold": 0.01},
            "input_files": {},
            "icd10_version": "2019",
            "icd11_version": "2026-01",
        }

        report_path = generate_report(metrics, details, metadata, tmp_path)
        content = report_path.read_text()

        assert "100" in content  # total_source
        assert "50" in content  # matched_source
        assert "50.0%" in content  # coverage

    def test_creates_multiple_files(self, tmp_path: Path) -> None:
        metrics = EvaluationMetrics(
            total_source=10,
            matched_source=5,
            coverage=0.5,
            exact_match_top1=0.3,
            exact_match_top5=0.6,
            exact_match_top10=0.8,
            precision_at1=0.35,
            recall_at1=0.25,
            abstained_count=1,
            abstained_pct=0.1,
            missing_in_gt=2,
        )
        details = []
        metadata = {
            "method": "test",
            "method_version": "1.0.0",
            "config": {},
            "input_files": {},
            "icd10_version": "2019",
            "icd11_version": "2026-01",
        }

        generate_report(metrics, details, metadata, tmp_path)
        files = list(tmp_path.glob("*"))
        assert len(files) >= 3  # report, metrics, details
