"""One extraction-grounded summary used for event candidate retrieval."""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EventSummary:
    news_id: uuid.UUID
    url: str
    text: str
    has_primary_event: bool
    published_at: datetime | None
    embedding: tuple[float, ...] = ()
    # The item reports a Russian normative act that reaches the company and calls for action.
    is_regulatory_alert: bool = False

    def with_embedding(self, embedding: list[float]) -> "EventSummary":
        return replace(self, embedding=tuple(embedding))
