"""Deterministic baseline matching using TF-IDF and cosine similarity.

This module implements a character n-gram TF-IDF matcher that proposes
ICD-11 candidates for each ICD-10 code.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class MatchConfig:
    """Configuration for the baseline matcher."""

    ngram_range: tuple[int, int] = (2, 4)
    top_k: int = 10
    abstain_threshold: float = 0.01
    max_features: int = 50000
    random_seed: int = 42


@dataclass
class MatchResult:
    """A single match result."""

    source_code: str
    target_code: str
    rank: int
    score: float
    probability: float
    abstain: bool


@dataclass
class MatchOutput:
    """Complete matching output."""

    results: list[MatchResult]
    config: MatchConfig
    source_count: int
    target_count: int
    abstained_count: int


def build_vectorizer(config: MatchConfig) -> TfidfVectorizer:
    """Build a TF-IDF vectorizer with character n-grams.

    Args:
        config: Match configuration.

    Returns:
        Fitted TfidfVectorizer.
    """
    return TfidfVectorizer(
        analyzer="char",
        ngram_range=config.ngram_range,
        max_features=config.max_features,
        lowercase=True,
        strip_accents=None,
        token_pattern=r"(?u)\b\w+\b",
    )


def compute_candidates(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    config: MatchConfig | None = None,
) -> MatchOutput:
    """Compute TF-IDF candidates for each source code.

    Args:
        source_df: ICD-10 DataFrame with 'code' and 'title_normalized' columns.
        target_df: ICD-11 DataFrame with 'code' and 'title_normalized' columns.
        config: Match configuration.

    Returns:
        MatchOutput with ranked candidates for each source.
    """
    if config is None:
        config = MatchConfig()

    # Filter to categories only
    source_cats = source_df[source_df["kind"] == "category"].copy()
    target_cats = target_df[target_df["kind"] == "category"].copy()

    # Remove entries without titles
    source_cats = source_cats[source_cats["title_normalized"].str.len() > 0]
    target_cats = target_cats[target_cats["title_normalized"].str.len() > 0]

    # Build TF-IDF matrix
    vectorizer = build_vectorizer(config)

    # Combine source and target texts for consistent vocabulary
    all_texts = pd.concat([source_cats["title_normalized"], target_cats["title_normalized"]])
    vectorizer.fit(all_texts)

    # Transform source and target
    source_vectors = vectorizer.transform(source_cats["title_normalized"])
    target_vectors = vectorizer.transform(target_cats["title_normalized"])

    # Compute similarity matrix
    sim_matrix = cosine_similarity(source_vectors, target_vectors)

    # Generate results
    results: list[MatchResult] = []

    for i, (_, source_row) in enumerate(source_cats.iterrows()):
        source_code = source_row["code"]

        # Get similarities for this source
        sims = sim_matrix[i]

        # Rank targets by similarity
        ranked_indices = np.argsort(sims)[::-1][: config.top_k]

        # Compute probabilities (relative scores)
        top_scores = sims[ranked_indices]
        score_sum = top_scores.sum()

        for rank, target_idx in enumerate(ranked_indices, start=1):
            score = float(sims[target_idx])
            target_code = target_cats.iloc[target_idx]["code"]

            # Compute relative probability
            probability = float(score / score_sum) if score_sum > 0 else 0.0

            # Check abstention
            abstain = score < config.abstain_threshold

            results.append(
                MatchResult(
                    source_code=source_code,
                    target_code=target_code,
                    rank=rank,
                    score=score,
                    probability=probability,
                    abstain=abstain,
                )
            )

    abstained = sum(1 for r in results if r.abstain)

    return MatchOutput(
        results=results,
        config=config,
        source_count=len(source_cats),
        target_count=len(target_cats),
        abstained_count=abstained,
    )


def results_to_dataframe(output: MatchOutput) -> pd.DataFrame:
    """Convert MatchOutput to a pandas DataFrame.

    Args:
        output: Match output.

    Returns:
        DataFrame with columns: source_code, target_code, rank, score,
        probability, abstain
    """
    return pd.DataFrame([vars(r) for r in output.results])


def get_top_predictions(output: MatchOutput, k: int = 1) -> pd.DataFrame:
    """Get top-k predictions per source code.

    Args:
        output: Match output.
        k: Number of top predictions to return.

    Returns:
        DataFrame with top-k predictions.
    """
    df = results_to_dataframe(output)
    return df[df["rank"] <= k]


def get_abstained_sources(output: MatchOutput) -> list[str]:
    """Get list of source codes that were abstained.

    Args:
        output: Match output.

    Returns:
        List of abstained source codes.
    """
    df = results_to_dataframe(output)
    abstained = df[df["abstain"] == True]["source_code"].unique()
    return sorted(abstained.tolist())
