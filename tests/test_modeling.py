"""Tests for deterministic baseline matching."""
from pathlib import Path

import pandas as pd
import pytest

from nomenclador_conceptos_luis.modeling import (
    MatchConfig,
    MatchOutput,
    MatchResult,
    compute_candidates,
    get_abstained_sources,
    get_top_predictions,
    results_to_dataframe,
)

RAW_DATA = Path("data/raw")


class TestMatchConfig:
    """Tests for MatchConfig."""

    def test_default_config(self) -> None:
        config = MatchConfig()
        assert config.ngram_range == (2, 4)
        assert config.top_k == 10
        assert config.abstain_threshold == 0.01

    def test_custom_config(self) -> None:
        config = MatchConfig(ngram_range=(2, 3), top_k=5)
        assert config.ngram_range == (2, 3)
        assert config.top_k == 5

    def test_deterministic(self) -> None:
        config1 = MatchConfig()
        config2 = MatchConfig()
        assert config1.ngram_range == config2.ngram_range
        assert config1.top_k == config2.top_k
        assert config1.abstain_threshold == config2.abstain_threshold


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_creation(self) -> None:
        result = MatchResult(
            source_code="A00.0",
            target_code="1A00.0",
            rank=1,
            score=0.85,
            probability=0.45,
            abstain=False,
        )
        assert result.source_code == "A00.0"
        assert result.target_code == "1A00.0"
        assert result.rank == 1
        assert result.score == 0.85
        assert result.probability == 0.45
        assert result.abstain is False

    def test_abstained(self) -> None:
        result = MatchResult(
            source_code="A00.0",
            target_code="1A00.0",
            rank=1,
            score=0.005,
            probability=1.0,
            abstain=True,
        )
        assert result.abstain is True


class TestMatchOutput:
    """Tests for MatchOutput dataclass."""

    def test_creation(self) -> None:
        output = MatchOutput(
            results=[],
            config=MatchConfig(),
            source_count=100,
            target_count=200,
            abstained_count=10,
        )
        assert output.source_count == 100
        assert output.target_count == 200
        assert output.abstained_count == 10
        assert len(output.results) == 0


class TestResultsToDataframe:
    """Tests for results_to_dataframe."""

    def test_conversion(self) -> None:
        output = MatchOutput(
            results=[
                MatchResult("A00.0", "1A00.0", 1, 0.85, 0.45, False),
                MatchResult("A00.0", "1A00.1", 2, 0.75, 0.35, False),
            ],
            config=MatchConfig(),
            source_count=1,
            target_count=2,
            abstained_count=0,
        )
        df = results_to_dataframe(output)
        assert len(df) == 2
        assert list(df.columns) == ["source_code", "target_code", "rank", "score", "probability", "abstain"]
        assert df.iloc[0]["source_code"] == "A00.0"
        assert df.iloc[0]["rank"] == 1


class TestGetTopPredictions:
    """Tests for get_top_predictions."""

    def test_top_1(self) -> None:
        output = MatchOutput(
            results=[
                MatchResult("A00.0", "1A00.0", 1, 0.85, 0.45, False),
                MatchResult("A00.0", "1A00.1", 2, 0.75, 0.35, False),
                MatchResult("A00.0", "1A00.2", 3, 0.65, 0.20, False),
            ],
            config=MatchConfig(),
            source_count=1,
            target_count=3,
            abstained_count=0,
        )
        top = get_top_predictions(output, k=1)
        assert len(top) == 1
        assert top.iloc[0]["rank"] == 1

    def test_top_2(self) -> None:
        output = MatchOutput(
            results=[
                MatchResult("A00.0", "1A00.0", 1, 0.85, 0.45, False),
                MatchResult("A00.0", "1A00.1", 2, 0.75, 0.35, False),
                MatchResult("A00.0", "1A00.2", 3, 0.65, 0.20, False),
            ],
            config=MatchConfig(),
            source_count=1,
            target_count=3,
            abstained_count=0,
        )
        top = get_top_predictions(output, k=2)
        assert len(top) == 2
        assert set(top["rank"]) == {1, 2}


class TestGetAbstainedSources:
    """Tests for get_abstained_sources."""

    def test_with_abstentions(self) -> None:
        output = MatchOutput(
            results=[
                MatchResult("A00.0", "1A00.0", 1, 0.85, 0.45, False),
                MatchResult("A01.0", "1A01.0", 1, 0.005, 1.0, True),
                MatchResult("A02.0", "1A02.0", 1, 0.80, 1.0, False),
            ],
            config=MatchConfig(),
            source_count=3,
            target_count=3,
            abstained_count=1,
        )
        abstained = get_abstained_sources(output)
        assert abstained == ["A01.0"]

    def test_no_abstentions(self) -> None:
        output = MatchOutput(
            results=[
                MatchResult("A00.0", "1A00.0", 1, 0.85, 0.45, False),
                MatchResult("A01.0", "1A01.0", 1, 0.80, 0.55, False),
            ],
            config=MatchConfig(),
            source_count=2,
            target_count=2,
            abstained_count=0,
        )
        abstained = get_abstained_sources(output)
        assert abstained == []
