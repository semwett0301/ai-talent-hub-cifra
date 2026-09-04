"""Collector ports — the pull/push strategies, implemented in infrastructure.

`Source` is the persistence schema (ORM), used directly here by design (no separate
domain entity). `NewsItem` is the domain entity every collector emits.
"""

from typing import Protocol

from source_service.domain.schemas import NewsItem, Source


class PullCollector(Protocol):
    """We go and fetch on a timer (RSS, Web)."""

    async def fetch(self, source: Source) -> list[NewsItem]: ...


class PushCollector(Protocol):
    """The source delivers to us; we subscribe/unsubscribe (Telegram)."""

    async def subscribe(self, source: Source) -> None: ...

    async def unsubscribe(self, source: Source) -> None: ...
