"""NpaCatalog — the acts catalog: list everything, get one, create one."""

import uuid

from domain.core.logging import get_logger
from domain.entities.npa import NpaDTO
from domain.schemas import Npa

from npa_service.application.ports import NpaRepository

logger = get_logger(__name__)


class NpaCatalog:
    def __init__(self, repo: NpaRepository) -> None:
        self.__repo = repo

    async def list(self, limit: int, offset: int) -> list[Npa]:
        return await self.__repo.list_all(limit, offset)

    async def get(self, npa_id: uuid.UUID) -> Npa | None:
        return await self.__repo.get(npa_id)

    async def create(self, act: NpaDTO) -> Npa:
        """Store the act; `NpaAlreadyExistsError` propagates for a repeated `url`."""
        stored = await self.__repo.add(act)

        logger.info("npa created: id=%s url=%s", stored.id, stored.url)
        return stored
