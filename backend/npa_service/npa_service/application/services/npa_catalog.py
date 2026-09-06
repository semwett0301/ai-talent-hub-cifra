"""Read-only NPA catalog."""

import uuid

from common.schemas import Npa, NpaVersion

from npa_service.application.ports import NpaRepository


class NpaCatalog:
    def __init__(self, repo: NpaRepository) -> None:
        self.__repo = repo

    async def list_all(self, limit: int, offset: int) -> list[Npa]:
        return await self.__repo.list_all(limit, offset)

    async def get(self, npa_id: uuid.UUID) -> Npa | None:
        return await self.__repo.get(npa_id)

    async def list_versions(self, npa_id: uuid.UUID) -> list[NpaVersion]:
        return await self.__repo.list_versions(npa_id)
