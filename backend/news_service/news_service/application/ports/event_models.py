"""LLM contract for event extraction, per-news summaries, and membership alignment."""

import uuid
from typing import Protocol

from news_service.domain.dedup import (
    EventSummary,
    MembershipDecision,
    NewsTarget,
    Precluster,
)


class EventModels(Protocol):
    async def summarize(self, items: list[NewsTarget]) -> list[EventSummary]: ...

    async def align(
        self, preclusters: list[Precluster]
    ) -> list[dict[uuid.UUID, MembershipDecision]]: ...
