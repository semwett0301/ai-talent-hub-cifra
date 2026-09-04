"""Collector ports — the pull/push strategies, implemented in infrastructure.

`Source` is the persistence schema (ORM), used directly here by design (no separate
domain entity). `NewsDTO` (from `domain.entities.news`) is the shared message contract every
collector emits.
"""

from typing import Protocol

from domain.entities.news import NewsDTO
from domain.schemas import Source


class PullCollector(Protocol):
    """We go and fetch on a timer (RSS, Web)."""

    async def fetch(self, source: Source) -> list[NewsDTO]: ...


class PushCollector(Protocol):
    """The source delivers to us; we subscribe/unsubscribe (Telegram)."""

    async def subscribe(self, source: Source) -> None: ...

    async def unsubscribe(self, source: Source) -> None: ...
