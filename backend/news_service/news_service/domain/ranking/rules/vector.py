"""Dense relevance calculations over normalized summary embeddings."""

import math
from collections.abc import Sequence

from news_service.domain.ranking import ClusterRankingTarget, Facet

DENSE_MAX_WEIGHT = 0.70
DENSE_TOP_TWO_WEIGHT = 0.30


def calculate_dense_context(
    target: ClusterRankingTarget,
    facets: tuple[Facet, ...],
    facet_vectors: list[list[float]],
) -> tuple[float, str]:
    scores = [_facet_score(vector, target.embeddings) for vector in facet_vectors]
    if not scores:
        return 0.0, ""
    best_index = max(range(len(scores)), key=scores.__getitem__)
    return scores[best_index], facets[best_index].name


def _facet_score(facet_vector: Sequence[float], embeddings: tuple[tuple[float, ...], ...]) -> float:
    similarities = [_cosine(facet_vector, embedding) for embedding in embeddings]
    if not similarities:
        return 0.0
    ordered = sorted(similarities, reverse=True)
    top_two_mean = sum(ordered[:2]) / min(2, len(ordered))
    return DENSE_MAX_WEIGHT * ordered[0] + DENSE_TOP_TWO_WEIGHT * top_two_mean


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector dimensions differ")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    denominator = left_norm * right_norm
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    return numerator / denominator if denominator else 0.0
