"""Deterministic product formula and categories from the ranking reference."""

from news_service.domain.ranking.relevance_category import RelevanceCategory

WEIGHT_IMPACT = 0.30
WEIGHT_BM25 = 0.05625
WEIGHT_URGENCY = 0.0375
WEIGHT_SOURCE = 0.015
BM25_SATURATION = 10.0
RELEVANT_SCORE = 50.0
IMPORTANT_SCORE = 65.0
ATTENTION_SCORE = 80.0
RERANKER_WEIGHT = 0.20
RERANKER_NEUTRAL = 0.50


def calculate_relevance(impact: int, urgency: int, source: int, bm25_score: float) -> float:
    bm25_component = calculate_bm25_component(bm25_score)
    effective_urgency = urgency if impact >= 2 else 0
    active_weight = WEIGHT_IMPACT + WEIGHT_BM25 + WEIGHT_URGENCY
    weighted = (
        WEIGHT_IMPACT * impact
        + WEIGHT_BM25 * bm25_component
        + WEIGHT_URGENCY * effective_urgency
        + WEIGHT_SOURCE * (source - 2)
    )
    return _clamp(weighted / active_weight / 3.0 * 100.0, 0.0, 100.0)


def calculate_bm25_component(score: float) -> float:
    positive = max(0.0, score)
    return 3.0 * positive / (positive + BM25_SATURATION)


def categorize_relevance(score: float) -> RelevanceCategory:
    if score >= ATTENTION_SCORE:
        return RelevanceCategory.ATTENTION
    if score >= IMPORTANT_SCORE:
        return RelevanceCategory.IMPORTANT
    if score >= RELEVANT_SCORE:
        return RelevanceCategory.RELEVANT
    return RelevanceCategory.LOW


def combine_context(dense_score: float, reranker_score: float) -> float:
    adjusted = dense_score + RERANKER_WEIGHT * (reranker_score - RERANKER_NEUTRAL)
    return _clamp(adjusted, 0.0, 1.0)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
