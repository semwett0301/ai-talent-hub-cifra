"""Repository ports — data access contracts, implemented in infrastructure."""

import uuid
from typing import Protocol

from common.entities.news import SourceType
from common.schemas import Source


class SourceRepository(Protocol):
    """Persistence operations over sources; mutations commit.

    A source and its feed URLs (`rss_links`) are written together: `create` stores both
    under one commit, `update` replaces the feed list when `feed_urls` is given and
    leaves it alone when it is `None`.
    """

    async def list_all(self) -> list[Source]: ...

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]: ...

    async def get(self, source_id: uuid.UUID) -> Source | None: ...

    async def create(self, data: dict, feed_urls: list[str]) -> Source: ...

    async def update(
        self, source: Source, data: dict, feed_urls: list[str] | None = None
    ) -> Source: ...

    async def delete(self, source: Source) -> None: ...
