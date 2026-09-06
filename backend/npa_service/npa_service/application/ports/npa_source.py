"""Port for reading the current state of a State Duma bill."""

from typing import Protocol

from npa_service.domain import BillSnapshot


class NpaSource(Protocol):
    async def fetch(self, url: str) -> BillSnapshot: ...
