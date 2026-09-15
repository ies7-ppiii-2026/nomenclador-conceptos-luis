"""Tests for canonical data loaders."""
from pathlib import Path

import pandas as pd
import pytest

from nomenclador_conceptos_luis.data import (
    load_icd10,
    load_icd11,
    load_icd11_with_parent_codes,
    normalize_text,
    validate_icd10,
    validate_icd11,
)

RAW_DATA = Path("data/raw")


class TestNormalizeText:
    """Tests for text normalization."""

    def test_strips_whitespace(self) -> None:
        assert normalize_text("  hello  ") == "hello"

    def test_collapses_spaces(self) -> None:
        assert normalize_text("hello   world") == "hello world"

    def test_lowercases(self) -> None:
        assert normalize_text("HELLO World") == "hello world"

    def test_deterministic(self) -> None:
        text = "  Cholera due to Vibrio cholerae  "
        assert normalize_text(text) == normalize_text(text)


class TestLoadICD10:
    """Tests for ICD-10 loader."""

    @pytest.mark.skipif(
        not (RAW_DATA / "icd10/icd102019en.xml").exists(),
        reason="ICD-10 data not available",
    )
    def test_loads_data(self) -> None:
        df = load_icd10(RAW_DATA / "icd10/icd102019en.xml")
        assert len(df) > 0
        assert "code" in df.columns
        assert "title" in df.columns
        assert "kind" in df.columns
        assert "parent_code" in df.columns
        assert "title_normalized" in df.columns

    @pytest.mark.skipif(
        not (RAW_DATA / "icd10/icd102019en.xml").exists(),
        reason="ICD-10 data not available",
    )
    def test_has_categories(self) -> None:
        df = load_icd10(RAW_DATA / "icd10/icd102019en.xml")
        categories = df[df["kind"] == "category"]
        assert len(categories) > 0

    @pytest.mark.skipif(
        not (RAW_DATA / "icd10/icd102019en.xml").exists(),
        reason="ICD-10 data not available",
    )
    def test_code_format(self) -> None:
        df = load_icd10(RAW_DATA / "icd10/icd102019en.xml")
        # ICD-10 codes should be like A00, A00.0, etc.
        sample = df[df["kind"] == "category"]["code"].head(10)
        for code in sample:
            assert len(code) >= 3, f"Code too short: {code}"

    @pytest.mark.skipif(
        not (RAW_DATA / "icd10/icd102019en.xml").exists(),
        reason="ICD-10 data not available",
    )
    def test_validation(self) -> None:
        df = load_icd10(RAW_DATA / "icd10/icd102019en.xml")
        warnings = validate_icd10(df)
        # Should have no critical warnings
        for w in warnings:
            assert "missing code" not in w.lower()


class TestLoadICD11:
    """Tests for ICD-11 loader."""

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_loads_data(self) -> None:
        df = load_icd11(RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt")
        assert len(df) > 0
        assert "code" in df.columns
        assert "title" in df.columns
        assert "kind" in df.columns
        assert "title_normalized" in df.columns

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_has_categories(self) -> None:
        df = load_icd11(RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt")
        categories = df[df["kind"] == "category"]
        assert len(categories) > 0

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_code_format(self) -> None:
        df = load_icd11(RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt")
        # ICD-11 codes should be like 1A00, 1A00.0, etc.
        sample = df[df["kind"] == "category"]["code"].head(10)
        for code in sample:
            assert len(code) >= 3, f"Code too short: {code}"

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_title_cleaned(self) -> None:
        df = load_icd11(RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt")
        # Titles should not start with dashes
        sample = df["title"].head(20)
        for title in sample:
            assert not title.startswith("-"), f"Title still has dashes: {title}"

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_validation(self) -> None:
        df = load_icd11(RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt")
        warnings = validate_icd11(df)
        # Should have no critical warnings
        for w in warnings:
            assert "missing code" not in w.lower()


class TestLoadICD11WithParentCodes:
    """Tests for ICD-11 loader with parent code resolution."""

    @pytest.mark.skipif(
        not (RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt").exists(),
        reason="ICD-11 data not available",
    )
    def test_resolves_parents(self) -> None:
        df = load_icd11_with_parent_codes(
            RAW_DATA / "icd11/SimpleTabulation-ICD-11-MMS-en.txt"
        )
        # Should have parent_code column
        assert "parent_code" in df.columns
        # Some records should have parent codes
        has_parent = df["parent_code"].notna() & (df["parent_code"] != "")
        assert has_parent.any()
