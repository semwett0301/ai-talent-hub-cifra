"""Persistable ranking result calculated once for a deduplicated cluster."""

import uuid
from dataclasses import dataclass
from typing import Any

from news_service.domain.ranking.relevance_category import RelevanceCategory


@dataclass(frozen=True, slots=True)
class RankingResult:
    cluster_id: uuid.UUID
    relevance_score: float
    category: RelevanceCategory
    context_score: float
    member_count: int
    details: dict[str, Any]
