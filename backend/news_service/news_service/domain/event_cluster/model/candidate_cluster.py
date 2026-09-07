"""A pgvector-retrieved cluster and its identity anchors."""

import uuid
from dataclasses import dataclass

from news_service.domain.event_summary.event_summary import EventSummary


@dataclass(frozen=True, slots=True)
class CandidateCluster:
    cluster_id: uuid.UUID
    score: float
    anchors: tuple[EventSummary, ...]
