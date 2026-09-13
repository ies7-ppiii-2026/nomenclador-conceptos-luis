# Experiment Contract

**Version**: 1.0.0
**Date**: 2026-09-11
**Status**: Active

## Objective

Map ICD-10 codes to ICD-11 codes using automated techniques. The system proposes candidate ICD-11 codes for each ICD-10 input, ranked by similarity score.

## Scope

- **Direction**: ICD-10 → ICD-11
- **Type**: Multi-label mapping (one ICD-10 can map to multiple ICD-11 codes)
- **Approach**: Text-based matching (no clinical validation in baseline)

## Input Specification

### Allowed Input Files

| Stage | Files Allowed | Files Excluded |
|-------|---------------|----------------|
| Inference | `data/raw/icd10/icd102019en.xml` | `data/raw/mapping/*` |
| Inference | `data/raw/icd11/SimpleTabulation-ICD-11-MMS-en.txt` | |
| Inference | `data/raw/icd11/SimpleTabulation-ICD-11-MMS-en.xlsx` | |
| Evaluation | `data/raw/mapping/10To11MapToOneCategory.txt` | |
| Evaluation | `data/raw/mapping/10To11MapToMultipleCategories.txt` | |

### Data Sources

- **ICD-10**: ClaML/XML format from WHO
- **ICD-11**: Tab-separated values (TSV) from WHO
- **Ground Truth**: Official WHO mapping files

## Output Specification

### Output Format

Each prediction must include:

| Field | Type | Description |
|-------|------|-------------|
| `source_code` | string | ICD-10 code (e.g., "A00.0") |
| `target_code` | string | ICD-11 code (e.g., "1A00.0") |
| `rank` | integer | Position in candidate list (1 = best) |
| `score` | float | Raw similarity score (0.0 - 1.0) |
| `probability` | float | Relative probability (normalized, sums to 1.0 within source) |
| `abstain` | boolean | True when evidence is insufficient |

### Output Rules

1. **Multi-label**: Each ICD-10 can have 0 or more ICD-11 candidates
2. **No forced 1:1**: The system does NOT force a single mapping
3. **Ranking**: Candidates are ranked by descending score
4. **Abstention**: When confidence is below threshold, mark as abstained
5. **Determinism**: Same inputs + same parameters = same output

## Probability Semantics

- Probabilities are **relative**, not clinically calibrated
- `probability` = `score / sum(scores_for_source)`
- Probabilities indicate ranking confidence, not clinical certainty
- Do NOT interpret as diagnostic probabilities

## Abstention Rules

A prediction is abstained when:
- No candidates exceed the similarity threshold
- The input text is empty or unparseable
- Fewer than N characters remain after normalization

## File Access Rules

### Inference Stage
- **READ**: `data/raw/icd10/*`, `data/raw/icd11/*`
- **FORBIDDEN**: `data/raw/mapping/*`
- **WRITE**: `data/processed/`, `reports/`

### Evaluation Stage
- **READ**: `data/raw/mapping/*`, inference output
- **WRITE**: `reports/`

## Normalization Rules

All text must be normalized deterministically:
1. Lowercase
2. Strip leading/trailing whitespace
3. Collapse multiple spaces to single space
4. Remove punctuation (optional, method-dependent)
5. Apply Unicode NFKD normalization

## Versioning

- Contract version follows semver
- Method version recorded in output metadata
- SHA-256 hashes of input files recorded per run

## Verification

### Input Validation
- Verify all required files exist before processing
- Verify XML is well-formed
- Verify TSV has expected columns
- Report missing entities (no code or title)

### Output Validation
- Verify output columns match specification
- Verify scores are in [0.0, 1.0] range
- Verify probabilities sum to 1.0 within source
- Verify deterministic output for same inputs
