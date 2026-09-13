"""Tests for experiment contract."""
from pathlib import Path


def test_contract_exists() -> None:
    """Verify contract document exists and is readable."""
    contract_path = Path("docs/contract.md")
    assert contract_path.exists(), "Contract document must exist"
    content = contract_path.read_text()
    assert len(content) > 0, "Contract must not be empty"


def test_contract_has_required_sections() -> None:
    """Verify contract contains all required sections."""
    contract_path = Path("docs/contract.md")
    content = contract_path.read_text()

    required_sections = [
        "Objective",
        "Input Specification",
        "Output Specification",
        "Probability Semantics",
        "Abstention Rules",
        "File Access Rules",
        "Normalization Rules",
        "Versioning",
    ]

    for section in required_sections:
        assert section in content, f"Contract missing required section: {section}"


def test_contract_defines_output_fields() -> None:
    """Verify contract defines all required output fields."""
    contract_path = Path("docs/contract.md")
    content = contract_path.read_text()

    required_fields = ["source_code", "target_code", "rank", "score", "probability", "abstain"]

    for field in required_fields:
        assert field in content, f"Contract missing output field: {field}"


def test_contract_has_version() -> None:
    """Verify contract has a version number."""
    contract_path = Path("docs/contract.md")
    content = contract_path.read_text()

    assert "Version" in content, "Contract must have a version"
    assert "1.0" in content, "Contract must have a version number"
