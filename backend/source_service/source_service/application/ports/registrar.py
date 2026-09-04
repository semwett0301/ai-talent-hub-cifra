"""Registrar port — the seam the CRUD use case depends on.

`register` reconciles one source to the runtime (schedule a pull, subscribe a
push, or drop it when disabled); `unregister` tears it down. Implemented by
`SourceRegistry`; keeps `SourceService` decoupled from the scheduling/subscription
mechanics (and easy to fake in tests).
"""

from typing import Protocol

from domain.schemas import Source


class SourceRegistrar(Protocol):
    """Reconciles a source to the runtime (schedule/subscribe) or removes it."""

    async def register(self, source: Source) -> None: ...

    async def unregister(self, source: Source) -> None: ...
