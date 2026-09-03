"""Repository ports — data access contracts, implemented in infrastructure."""

from __future__ import annotations

from typing import Protocol

from common.enums import SourceType

from source_service.infrastructure.persistence.schemas import Source


class SourceRepository(Protocol):
    """Persistence operations over sources; mutations commit."""

    async def list(self) -> list[Source]: ...

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]: ...

    async def get(self, source_id: int) -> Source | None: ...

    async def create(self, data: dict) -> Source: ...

    async def update(self, source: Source, data: dict) -> Source: ...

    async def delete(self, source: Source) -> None: ...
