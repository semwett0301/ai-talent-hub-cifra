"""One trusted cluster anchor set with summaries to screen for membership."""

import uuid
from dataclasses import dataclass

from news_service.domain.dedup.event_summary import EventSummary


@dataclass(frozen=True, slots=True)
class Precluster:
    cluster_id: uuid.UUID
    anchors: tuple[EventSummary, ...]
    candidates: tuple[EventSummary, ...]
