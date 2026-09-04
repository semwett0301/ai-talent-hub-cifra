"""Push aggregator — subscribes push sources (Telegram) on startup.

Collaborators (collectors, source loader) are injected from `deps`. Live
subscribe/unsubscribe on CRUD is a TODO; for now enabled push sources are
subscribed at startup.
"""

from common.core.logging import get_logger
from common.enums import SourceType

from source_service.application.ports import PushCollector, SourceRepository
from source_service.domain.schemas import Source

logger = get_logger(__name__)


class SubscriptionService:
    def __init__(
        self,
        push_collectors: dict[SourceType, PushCollector],
        repository: SourceRepository,
    ) -> None:
        self._push_collectors = push_collectors
        self._repository = repository

    async def load(self) -> None:
        for source in await self._repository.list_enabled():
            await self.subscribe(source)

    async def subscribe(self, source: Source) -> None:
        collector = self._push_collectors.get(source.type)
        if collector is not None:
            await collector.subscribe(source)

    async def unsubscribe(self, source: Source) -> None:
        collector = self._push_collectors.get(source.type)
        if collector is not None:
            await collector.unsubscribe(source)
