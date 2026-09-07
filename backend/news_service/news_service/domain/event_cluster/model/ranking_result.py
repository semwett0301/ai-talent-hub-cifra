"""Persistable ranking result calculated once for a deduplicated cluster."""

import uuid
from dataclasses import dataclass
from typing import Any

from news_service.domain.event_cluster.model.relevance_category import RelevanceCategory


@dataclass(frozen=True, slots=True)
class RankingResult:
    cluster_id: uuid.UUID
    relevance_score: float
    category: RelevanceCategory
    member_count: int
    details: dict[str, Any]
