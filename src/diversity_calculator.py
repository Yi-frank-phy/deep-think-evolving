from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class SimilarityAnalysis:
    """Container for similarity statistics computed from embedded strategies."""

    matrix: np.ndarray
    average_similarity: float
    diversity_score: float

    @property
    def is_valid(self) -> bool:
        return self.matrix.size > 0


def _prepare_embeddings(strategies: list[dict]) -> np.ndarray:
    if not strategies or not all("embedding" in s for s in strategies):
        return np.array([])

    embeddings = np.array([s["embedding"] for s in strategies], dtype=float)
    if embeddings.size == 0:
        return np.array([])

    return embeddings


def _normalise_embeddings(embeddings: np.ndarray) -> np.ndarray:
    if embeddings.size == 0:
        return embeddings

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    return embeddings / norms


def _compute_similarity_matrix(normalised_embeddings: np.ndarray) -> np.ndarray:
    if normalised_embeddings.size == 0:
        return np.array([])

    similarity_matrix = np.dot(normalised_embeddings, normalised_embeddings.T)
    np.clip(similarity_matrix, -1.0, 1.0, out=similarity_matrix)
    return similarity_matrix


def _compute_similarity_statistics(matrix: np.ndarray) -> tuple[float, float]:
    if matrix.size == 0:
        return 0.0, 0.0

    if matrix.shape[0] == 1:
        # Only one strategy: perfectly similar to itself, zero diversity.
        return 1.0, 0.0

    upper_triangle = matrix[np.triu_indices(matrix.shape[0], k=1)]
    if upper_triangle.size == 0:
        return 1.0, 0.0

    avg_similarity = float(np.mean(upper_triangle))
    diversity = float(max(0.0, min(1.0, 1.0 - avg_similarity)))
    return avg_similarity, diversity


def calculate_similarity_analysis(strategies: list[dict]) -> SimilarityAnalysis:
    """Return the similarity matrix together with aggregate diversity metrics."""

    embeddings = _prepare_embeddings(strategies)
    if embeddings.size == 0:
        print("Error: Input is not a valid list of embedded strategies.")
        empty_matrix = np.array([])
        return SimilarityAnalysis(empty_matrix, 0.0, 0.0)

    normalised = _normalise_embeddings(embeddings)
    similarity_matrix = _compute_similarity_matrix(normalised)

    average_similarity, diversity_score = _compute_similarity_statistics(similarity_matrix)

    return SimilarityAnalysis(
        matrix=similarity_matrix,
        average_similarity=average_similarity,
        diversity_score=diversity_score,
    )


def calculate_similarity_matrix(strategies: list[dict]) -> np.ndarray:
    """Backwards compatible wrapper returning only the similarity matrix."""

    return calculate_similarity_analysis(strategies).matrix


__all__ = [
    "SimilarityAnalysis",
    "calculate_similarity_analysis",
    "calculate_similarity_matrix",
]
