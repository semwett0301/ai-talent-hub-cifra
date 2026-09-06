"""Repository ports — data access contracts, implemented in infrastructure."""

import uuid
from datetime import datetime
from typing import Protocol

from common.entities.npa import NpaTrackingStatus
from common.schemas import Npa, NpaVersion

from npa_service.domain import BillSnapshot, TrackedUpdate


class NpaRepository(Protocol):
    """Persistence operations over legislative acts; mutations commit."""

    async def list_all(self, limit: int, offset: int) -> list[Npa]: ...

    async def get(self, npa_id: uuid.UUID) -> Npa | None: ...

    async def list_tracking(self) -> list[Npa]: ...

    async def list_versions(self, npa_id: uuid.UUID) -> list[NpaVersion]: ...

    async def add(
        self, snapshot: BillSnapshot, status: NpaTrackingStatus, initial_summary: str
    ) -> Npa: ...

    async def apply_update(self, npa_id: uuid.UUID, update: TrackedUpdate) -> Npa: ...

    async def mark_checked(
        self, npa_id: uuid.UUID, snapshot: BillSnapshot, checked_at: datetime
    ) -> None: ...
