"""Bounded pgvector lookup parameters for one pending event summary."""

import uuid
from dataclasses import dataclass

from news_service.domain.event_summary.event_summary import EventSummary


@dataclass(frozen=True, slots=True)
class CandidateQuery:
    summary: EventSummary
    available_pending_ids: tuple[uuid.UUID, ...]
    window_days: int
    limit: int
    minimum_score: float
