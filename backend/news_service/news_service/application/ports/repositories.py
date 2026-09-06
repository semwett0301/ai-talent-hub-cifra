"""Repository ports — data access contracts, implemented in infrastructure."""

import uuid
from typing import Protocol

from common.schemas import News

from news_service.application.ports.transaction import NewsTransaction


class NewsRepository(Protocol):
    """Persistence operations over news; mutations commit (except inside `begin()`)."""

    async def list_all(self, limit: int, offset: int) -> list[News]: ...

    def begin(self) -> NewsTransaction:
        """Open one transaction to stage mutations in; see `NewsTransaction`."""
        ...

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        """Set `is_alert = true` on one row; returns it, or None when the id is unknown."""
        ...
