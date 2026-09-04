"""CRUD use-cases over sources — orchestrates the repository port.

Every mutation reconciles the runtime through the injected `SourceRegistrar`:
create/update (re)register the source, delete unregisters it — so pull scheduling
and push subscriptions stay in sync without a restart.
"""

import uuid

from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.ports import SourceRegistrar, SourceRepository
from source_service.domain.schemas import Source


class SourceService:
    def __init__(self, repo: SourceRepository, registrar: SourceRegistrar) -> None:
        self._repo = repo
        self._registrar = registrar

    async def list(self) -> list[Source]:
        return await self._repo.list_all()

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get(source_id)

    async def create(self, payload: SourceCreate) -> Source:
        source = await self._repo.create(payload.model_dump())

        await self._registrar.register(source)
        return source

    async def update(self, source: Source, payload: SourceUpdate) -> Source:
        updated = await self._repo.update(source, payload.model_dump(exclude_unset=True))

        await self._registrar.register(updated)
        return updated

    async def delete(self, source: Source) -> None:
        await self._repo.delete(source)
        await self._registrar.unregister(source)
