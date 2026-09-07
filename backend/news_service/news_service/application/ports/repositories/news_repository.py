"""Repository port — data access over one unit of work, implemented in infrastructure."""

import uuid
from typing import Protocol

from common.entities.news import NewsDTO
from common.schemas import News

from news_service.application.dto.news import NewsQuery


class NewsRepository(Protocol):
    """One instance = one open unit of work (a request, a batch), scoped by the composition root.

    Writes are *staged*: nothing reaches the DB for good until `commit()`. The use case
    decides when that is — after every step it needs to succeed first (an external call,
    a whole batch) has succeeded. A unit of work that ends without `commit()` rolls back.
    """

    async def list_matching(self, query: NewsQuery) -> list[News]:
        """Rows matching `query`'s filters, one per event cluster (duplicates left out),
        newest publication first."""
        ...

    async def get(self, news_id: uuid.UUID) -> News | None: ...

    async def add_many(self, items: list[NewsDTO]) -> int:
        """Stage a batch insert, skipping urls already stored and items whose source is gone;
        returns the number of rows the insert added. Raises `NewsStoreError` if it fails."""
        ...

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        """Stage `is_alert = true` on one row; returns it, or None when the id is unknown."""
        ...

    async def mark_dismissed(self, news_id: uuid.UUID) -> News | None:
        """Stage `dismissed_at = now()` (kept if already set); None when the id is unknown."""
        ...

    async def mark_restored(self, news_id: uuid.UUID) -> News | None:
        """Stage `dismissed_at = NULL`; None when the id is unknown."""
        ...

    async def commit(self) -> None:
        """Persist everything staged so far. Raises `NewsStoreError` if the DB refuses."""
        ...
