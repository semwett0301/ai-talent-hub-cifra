"""Source registry — reconciles each source to the runtime.

The runtime side of a source, injected straight into the CRUD use case. Dispatches by
source type: pull sources (RSS/Web) get a periodic fetch→publish job through the
`JobScheduler` port, push sources (Telegram) get a live subscription. `register`
applies one source's desired state (schedule/subscribe when enabled, tear down when
disabled), `unregister` removes it, `load` bootstraps every enabled source at startup.
"""

import uuid
from dataclasses import dataclass

from common.core.logging import get_logger
from common.core.settings import SourceSchedulerSettings
from common.entities.news import SourceType
from common.schemas import Source

from source_service.application.ports.source import (
    JobScheduler,
    NewsPublisher,
    PullCollector,
    PushCollector,
    SourceRepository,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class SourceCollectors:
    """Where news comes from and where it goes: a collector per source type, plus the
    publisher every pull run feeds. Wired once in `deps`."""

    pull: dict[SourceType, PullCollector]
    push: dict[SourceType, PushCollector]
    publisher: NewsPublisher


class SourceRegistry:
    """Holds no scheduling mechanics of its own: it decides *what* a source's runtime
    state should be, the `JobScheduler` port decides how a recurrence is made."""

    def __init__(
        self,
        collectors: SourceCollectors,
        scheduler: JobScheduler,
        repository: SourceRepository,
        settings: SourceSchedulerSettings,
    ) -> None:
        self.__collectors = collectors
        self.__scheduler = scheduler
        self.__repository = repository
        self.__settings = settings

    async def load(self) -> None:
        sources = await self.__repository.list_enabled()
        logger.info("registry loading: sources=%d", len(sources))

        for source in sources:
            await self.register(source)

        logger.info("registry loaded: sources=%d", len(sources))

    async def register(self, source: Source) -> None:
        logger.info(
            "source registering: id=%s type=%s link=%s enabled=%s",
            source.id,
            source.type,
            source.link,
            source.is_enabled,
        )

        if source.type in self.__collectors.pull:
            self.__apply_schedule(source)
        elif source.type in self.__collectors.push:
            await self.__apply_subscription(source)
        else:
            logger.warning("source has no collector: type=%s link=%s", source.type, source.link)

    async def unregister(self, source: Source) -> None:
        logger.info(
            "source unregistering: id=%s type=%s link=%s", source.id, source.type, source.link
        )

        if source.type in self.__collectors.pull:
            self.__unschedule(source.id)
        elif source.type in self.__collectors.push:
            await self.__collectors.push[source.type].unsubscribe(source)

    def __apply_schedule(self, source: Source) -> None:
        if not source.is_enabled:
            self.__unschedule(source.id)
            return

        seconds = source.poll_interval_seconds or self.__settings.source_poll_interval_seconds
        self.__scheduler.schedule(source.id, seconds, self.__run)
        logger.info("pull source scheduled: id=%s every=%ss", source.id, seconds)

    async def __apply_subscription(self, source: Source) -> None:
        collector = self.__collectors.push[source.type]
        if source.is_enabled:
            await collector.subscribe(source)
        else:
            await collector.unsubscribe(source)

    def __unschedule(self, source_id: uuid.UUID) -> None:
        self.__scheduler.unschedule(source_id)
        logger.info("pull source unscheduled: id=%s", source_id)

    async def __run(self, source_id: uuid.UUID) -> None:
        source = await self.__repository.get(source_id)
        if source is None or not source.is_enabled:
            logger.info("pull run skipped: id=%s (gone or disabled)", source_id)
            return

        collector = self.__collectors.pull.get(source.type)
        if collector is None:
            logger.warning("pull run skipped: no collector for type=%s", source.type)
            return

        items = await collector.fetch(source)
        logger.info("pull run fetched: link=%s items=%d", source.link, len(items))

        published = await self.__collectors.publisher.publish_news(items)
        logger.info("pull run published: link=%s items=%d", source.link, published)
