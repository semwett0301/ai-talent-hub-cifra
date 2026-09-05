"""Repository ports — data access contracts, implemented in infrastructure."""

import uuid
from typing import Protocol

from domain.entities.npa import NpaDTO
from domain.schemas import Npa


class NpaRepository(Protocol):
    """Persistence operations over legislative acts; mutations commit."""

    async def list_all(self, limit: int, offset: int) -> list[Npa]: ...

    async def get(self, npa_id: uuid.UUID) -> Npa | None: ...

    async def add(self, act: NpaDTO) -> Npa:
        """Insert one act and return the stored row. Raises `NpaAlreadyExistsError`
        when an act with the same `url` is already stored."""
        ...
