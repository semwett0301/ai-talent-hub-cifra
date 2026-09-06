"""A pgvector-retrieved cluster and its identity anchors."""

import uuid
from dataclasses import dataclass

from news_service.domain.dedup.event_summary import EventSummary


@dataclass(frozen=True, slots=True)
class CandidateCluster:
    cluster_id: uuid.UUID
    score: float
    anchors: tuple[EventSummary, ...]
