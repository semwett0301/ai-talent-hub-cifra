"""Repository ports — data access contracts, implemented in infrastructure."""

import uuid
from typing import Protocol

from domain.entities.news import NewsDTO
from domain.schemas import News

from news_service.application.ports.transaction import NewsTransaction


class NewsRepository(Protocol):
    """Persistence operations over news; mutations commit (except inside `begin()`)."""

    async def list_all(self, limit: int, offset: int) -> list[News]: ...

    def begin(self) -> NewsTransaction:
        """Open one transaction to stage mutations in; see `NewsTransaction`."""
        ...

    async def add_many(self, items: list[NewsDTO]) -> int:
        """Insert a batch in one transaction, skipping urls already stored; returns
        the number actually inserted. Raises `NewsStoreError` if the write fails."""
        ...

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        """Set `is_alert = true` on one row; returns it, or None when the id is unknown."""
        ...
