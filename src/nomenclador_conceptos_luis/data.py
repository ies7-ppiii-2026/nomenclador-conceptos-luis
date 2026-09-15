"""Canonical data loaders for ICD-10 and ICD-11.

This module provides deterministic loaders that extract codes, titles,
types, and hierarchy from the raw data files.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ICD10Record:
    """A single ICD-10 concept."""

    code: str
    title: str
    kind: str  # chapter, block, category
    parent_code: str | None


@dataclass(frozen=True)
class ICD11Record:
    """A single ICD-11 concept."""

    code: str
    title: str
    kind: str  # chapter, block, category
    parent_code: str | None
    foundation_uri: str
    linearization_uri: str
    is_residual: bool


def normalize_text(text: str) -> str:
    """Normalize text deterministically.

    Rules (from contract):
    1. Strip leading/trailing whitespace
    2. Collapse multiple spaces to single space
    3. Lowercase
    """
    text = text.strip()
    text = " ".join(text.split())
    text = text.lower()
    return text


def load_icd10(xml_path: Path) -> pd.DataFrame:
    """Load ICD-10 data from ClaML XML file.

    Args:
        xml_path: Path to the ICD-10 XML file.

    Returns:
        DataFrame with columns: code, title, kind, parent_code, title_normalized
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    records: list[ICD10Record] = []

    for elem in root.findall(".//Class"):
        code = elem.get("code", "")
        kind = elem.get("kind", "")

        # Get parent code
        super_class = elem.find("SuperClass")
        parent_code = super_class.get("code") if super_class is not None else None

        # Get preferred title
        title = ""
        for rubric in elem.findall("Rubric"):
            if rubric.get("kind") == "preferred":
                label = rubric.find("Label")
                if label is not None and label.text:
                    title = label.text.strip()
                    break

        # If no preferred, try inclusion
        if not title:
            for rubric in elem.findall("Rubric"):
                if rubric.get("kind") == "inclusion":
                    label = rubric.find("Label")
                    if label is not None and label.text:
                        title = label.text.strip()
                        break

        records.append(
            ICD10Record(
                code=code,
                title=title,
                kind=kind,
                parent_code=parent_code,
            )
        )

    df = pd.DataFrame([vars(r) for r in records])
    df["title_normalized"] = df["title"].apply(normalize_text)

    return df


def load_icd11(tsv_path: Path) -> pd.DataFrame:
    """Load ICD-11 data from TSV file.

    Args:
        tsv_path: Path to the ICD-11 TSV file.

    Returns:
        DataFrame with columns: code, title, kind, parent_code,
        foundation_uri, linearization_uri, is_residual, title_normalized
    """
    df = pd.read_csv(
        tsv_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )

    # Rename columns for consistency
    column_map = {
        "Code": "code",
        "Title": "title",
        "ClassKind": "kind",
        "Parent": "parent_uri",
        "Foundation URI": "foundation_uri",
        "Linearization URI": "linearization_uri",
        "IsResidual": "is_residual",
    }
    df = df.rename(columns=column_map)

    # Keep only relevant columns
    relevant_cols = ["code", "title", "kind", "parent_uri", "foundation_uri",
                     "linearization_uri", "is_residual"]
    df = df[[c for c in relevant_cols if c in df.columns]]

    # Extract parent code from URI
    def extract_parent_code(uri: str) -> str | None:
        if not uri or pd.isna(uri):
            return None
        # URI format: http://id.who.int/icd/entity/123456
        # We need to match by linearization URI, not entity URI
        return None  # Will be resolved after loading

    df["parent_code"] = df["parent_uri"].apply(extract_parent_code)

    # Clean title: remove leading dashes and normalize
    def clean_title(title: str) -> str:
        title = title.lstrip("- ").strip()
        return title

    df["title"] = df["title"].apply(clean_title)
    df["title_normalized"] = df["title"].apply(normalize_text)

    # Convert is_residual to boolean
    df["is_residual"] = df["is_residual"].map({"True": True, "False": False, "": False})

    return df


def load_icd11_with_parent_codes(tsv_path: Path) -> pd.DataFrame:
    """Load ICD-11 data and resolve parent codes.

    This builds a lookup from foundation URI to code, then resolves
    parent references.

    Args:
        tsv_path: Path to the ICD-11 TSV file.

    Returns:
        DataFrame with resolved parent_code column.
    """
    df = load_icd11(tsv_path)

    # Build foundation URI to code lookup
    uri_to_code = dict(zip(df["foundation_uri"], df["code"]))

    # Resolve parent codes
    def resolve_parent(uri: str) -> str | None:
        if not uri or pd.isna(uri) or uri == "":
            return None
        return uri_to_code.get(uri)

    df["parent_code"] = df["parent_uri"].apply(resolve_parent)

    return df


def validate_icd10(df: pd.DataFrame) -> list[str]:
    """Validate ICD-10 data quality.

    Returns:
        List of warning messages.
    """
    warnings: list[str] = []

    # Check for missing codes
    missing_code = df[df["code"].isna() | (df["code"] == "")]
    if len(missing_code) > 0:
        warnings.append(f"Found {len(missing_code)} records with missing code")

    # Check for missing titles
    missing_title = df[df["title"].isna() | (df["title"] == "")]
    if len(missing_title) > 0:
        warnings.append(f"Found {len(missing_title)} records with missing title")
        for _, row in missing_title.head(5).iterrows():
            warnings.append(f"  - code={row['code']}, kind={row['kind']}")

    # Check for duplicate codes
    dupes = df[df["code"].duplicated(keep=False)]
    if len(dupes) > 0:
        warnings.append(f"Found {len(dupes)} duplicate codes")

    return warnings


def validate_icd11(df: pd.DataFrame) -> list[str]:
    """Validate ICD-11 data quality.

    Note: Chapters and blocks may not have codes in the TSV format.
    This is expected behavior, not an error.

    Returns:
        List of warning messages.
    """
    warnings: list[str] = []

    # Check for missing codes (only for categories, not chapters/blocks)
    categories = df[df["kind"] == "category"]
    missing_code = categories[categories["code"].isna() | (categories["code"] == "")]
    if len(missing_code) > 0:
        warnings.append(f"Found {len(missing_code)} categories with missing code")

    # Check for missing titles
    missing_title = df[df["title"].isna() | (df["title"] == "")]
    if len(missing_title) > 0:
        warnings.append(f"Found {len(missing_title)} records with missing title")

    # Check for duplicate codes (only among non-empty codes)
    coded = df[df["code"] != ""]
    dupes = coded[coded["code"].duplicated(keep=False)]
    if len(dupes) > 0:
        warnings.append(f"Found {len(dupes)} duplicate codes")

    return warnings
