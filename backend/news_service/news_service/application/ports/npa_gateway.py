"""NpaGateway port — the outbound integration with `npa_service`."""

import uuid
from typing import Protocol

from domain.entities.npa import NpaDTO


class NpaGateway(Protocol):
    """Registers legislative acts in `npa_service` over its HTTP API."""

    async def create(self, act: NpaDTO) -> uuid.UUID:
        """Create the act remotely and return its id. Raises `NpaConflictError` when
        `npa_service` already holds that `url`, `NpaGatewayError` on any other failure
        (unreachable, timeout, non-2xx) — so the caller can roll back."""
        ...
