"""One extraction-grounded summary used for event candidate retrieval."""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class EventSummary:
    news_id: uuid.UUID
    url: str
    text: str
    extraction: dict[str, Any]
    published_at: datetime | None
    embedding: tuple[float, ...] = ()

    @property
    def has_primary_event(self) -> bool:
        return bool(self.extraction.get("primary_event_found"))

    def with_embedding(self, embedding: list[float]) -> "EventSummary":
        return replace(self, embedding=tuple(embedding))
