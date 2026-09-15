# Advanced Matching Techniques

**Status**: Deferred
**Date**: 2026-09-11
**Reason**: Awaiting evaluation results from baseline (Issue #6)

## Current State

The TF-IDF baseline has been implemented and is ready for evaluation.
Advanced techniques should only be explored if the baseline analysis
shows significant gaps that text-based matching cannot address.

## Potential Techniques (Future)

### 1. Hierarchical Rules

Use ICD-10/ICD-11 chapter/block structure to constrain matches.
For example, infectious diseases should only map to infectious diseases.

**Pros**:
- Reduces false positives
- Leverages existing taxonomy
- Deterministic

**Cons**:
- Requires manual rule definition
- May miss cross-chapter mappings
- Complex to maintain

### 2. Embeddings

Use pre-trained medical embeddings (e.g., SapBERT, PubMedBERT)
for semantic similarity.

**Pros**:
- Captures semantic equivalence
- Handles synonyms and abbreviations
- Can discover non-obvious mappings

**Cons**:
- Non-deterministic (model-dependent)
- Requires GPU for large-scale inference
- May not align with WHO classification logic

### 3. Record Linkage (Splink)

Use probabilistic record linkage for fuzzy matching.

**Pros**:
- Handles typos and variations
- Configurable thresholds
- Well-studied in epidemiology

**Cons**:
- Not designed for semantic mapping
- Requires training data
- May not capture clinical equivalence

## Decision Criteria

Advanced techniques should be explored when:

1. Baseline coverage < 60%
2. Baseline top-10 accuracy < 70%
3. Error analysis reveals systematic gaps
4. Clinical validation requires higher precision

## Next Steps

1. Run baseline evaluation (Issue #6)
2. Analyze error patterns
3. Identify specific gaps
4. Select technique based on gap analysis
5. Implement and compare against baseline
