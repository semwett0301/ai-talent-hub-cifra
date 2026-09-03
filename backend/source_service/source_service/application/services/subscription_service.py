"""Push aggregator — subscribes push sources (Telegram) on startup.

Collaborators (collectors, source loader) are injected from `deps`. Live
subscribe/unsubscribe on CRUD is a TODO; for now enabled push sources are
subscribed at startup.
"""

from collections.abc import Awaitable, Callable

from common.core.logging import get_logger
from common.enums import SourceType

from source_service.application.ports import PushCollector
from source_service.infrastructure.persistence.schemas import Source

logger = get_logger(__name__)


class SubscriptionService:
    def __init__(
        self,
        push_collectors: dict[SourceType, PushCollector],
        load_sources: Callable[[], Awaitable[list[Source]]],
    ) -> None:
        self._push_collectors = push_collectors
        self._load_sources = load_sources

    async def load(self) -> None:
        for source in await self._load_sources():
            await self.subscribe(source)

    async def subscribe(self, source: Source) -> None:
        collector = self._push_collectors.get(source.type)
        if collector is not None:
            await collector.subscribe(source)

    async def unsubscribe(self, source: Source) -> None:
        collector = self._push_collectors.get(source.type)
        if collector is not None:
            await collector.unsubscribe(source)
