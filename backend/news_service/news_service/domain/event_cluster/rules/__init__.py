"""Deterministic rules that judge an `EventCluster`."""

from news_service.domain.event_cluster.rules.bm25 import Bm25, calculate_bm25_scores
from news_service.domain.event_cluster.rules.membership import (
    combine_decisions,
    normalize_decision,
)
from news_service.domain.event_cluster.rules.scoring import (
    calculate_bm25_component,
    calculate_relevance,
    categorize_relevance,
)

__all__ = [
    "Bm25",
    "calculate_bm25_component",
    "calculate_bm25_scores",
    "calculate_relevance",
    "categorize_relevance",
    "combine_decisions",
    "normalize_decision",
]
