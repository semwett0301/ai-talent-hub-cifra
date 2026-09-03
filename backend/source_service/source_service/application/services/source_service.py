"""CRUD use-cases over sources — orchestrates the repository port."""

from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.ports import SourceRepository
from source_service.infrastructure.persistence.schemas import Source


class SourceService:
    def __init__(self, repo: SourceRepository) -> None:
        self._repo = repo

    async def list(self) -> list[Source]:
        return await self._repo.list()

    async def get(self, source_id: int) -> Source | None:
        return await self._repo.get(source_id)

    async def create(self, payload: SourceCreate) -> Source:
        return await self._repo.create(payload.model_dump())

    async def update(self, source: Source, payload: SourceUpdate) -> Source:
        return await self._repo.update(source, payload.model_dump(exclude_unset=True))

    async def delete(self, source: Source) -> None:
        await self._repo.delete(source)
