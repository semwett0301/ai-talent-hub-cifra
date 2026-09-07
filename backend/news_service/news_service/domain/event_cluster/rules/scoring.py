"""Deterministic product formula and categories from the ranking reference."""

from news_service.domain.event_cluster.model.relevance_category import RelevanceCategory

WEIGHT_IMPACT = 0.30
WEIGHT_BM25 = 0.05625
WEIGHT_URGENCY = 0.0375
WEIGHT_SOURCE = 0.015
BM25_SATURATION = 10.0
# Impact alone yields ~25 per grade (1 → 25, 2 → 51, 3 → 76 before BM25/urgency), so the
# thresholds map one impact grade to one category: any evidenced consequence is relevant.
RELEVANT_SCORE = 25.0
IMPORTANT_SCORE = 50.0
ATTENTION_SCORE = 75.0


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


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
