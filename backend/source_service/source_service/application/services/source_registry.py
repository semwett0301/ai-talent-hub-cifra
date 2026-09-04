"""Source registry — reconciles each source to the runtime.

The single `SourceRegistrar` the CRUD use-case depends on. Dispatches by source
type: pull sources (RSS/Web) get a periodic fetch→publish job on APScheduler, push
sources (Telegram) get a live subscription. `register` applies one source's desired
state (schedule/subscribe when enabled, tear down when disabled), `unregister`
removes it, `load` bootstraps every enabled source at startup.
"""

import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from domain.core.logging import get_logger
from domain.entities.news import SourceType
from domain.schemas import Source

from source_service.application.ports import (
    NewsPublisher,
    PullCollector,
    PushCollector,
    SourceRegistrar,
    SourceRepository,
)

logger = get_logger(__name__)

DEFAULT_INTERVAL_SECONDS = 300
JOB_ID_PREFIX = "src-"


class SourceRegistry(SourceRegistrar):
    def __init__(
        self,
        publisher: NewsPublisher,
        pull_collectors: dict[SourceType, PullCollector],
        push_collectors: dict[SourceType, PushCollector],
        repository: SourceRepository,
    ) -> None:
        self._publisher = publisher
        self._pull_collectors = pull_collectors
        self._push_collectors = push_collectors
        self._repository = repository
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    async def load(self) -> None:
        sources = await self._repository.list_enabled()
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

        if source.type in self._pull_collectors:
            self.__apply_schedule(source)
        elif source.type in self._push_collectors:
            await self.__apply_subscription(source)
        else:
            logger.warning("source has no collector: type=%s link=%s", source.type, source.link)

    async def unregister(self, source: Source) -> None:
        logger.info(
            "source unregistering: id=%s type=%s link=%s", source.id, source.type, source.link
        )

        if source.type in self._pull_collectors:
            self.__unschedule(source.id)
        elif source.type in self._push_collectors:
            await self._push_collectors[source.type].unsubscribe(source)

    def __apply_schedule(self, source: Source) -> None:
        if source.is_enabled:
            self.__schedule(source.id, source.poll_interval_seconds)
        else:
            self.__unschedule(source.id)

    async def __apply_subscription(self, source: Source) -> None:
        collector = self._push_collectors[source.type]
        if source.is_enabled:
            await collector.subscribe(source)
        else:
            await collector.unsubscribe(source)

    def __schedule(self, source_id: uuid.UUID, interval: int | None) -> None:
        seconds = interval or DEFAULT_INTERVAL_SECONDS
        logger.info("pull source scheduled: id=%s every=%ss", source_id, seconds)

        self._scheduler.add_job(
            self.__run,
            "interval",
            seconds=seconds,
            args=[source_id],
            id=self.__job_id(source_id),
            replace_existing=True,
        )

    def __unschedule(self, source_id: uuid.UUID) -> None:
        if self._scheduler.get_job(self.__job_id(source_id)) is None:
            return

        self._scheduler.remove_job(self.__job_id(source_id))
        logger.info("pull source unscheduled: id=%s", source_id)

    def __job_id(self, source_id: uuid.UUID) -> str:
        return f"{JOB_ID_PREFIX}{source_id}"

    async def __run(self, source_id: uuid.UUID) -> None:
        source = await self._repository.get(source_id)
        if source is None or not source.is_enabled:
            logger.info("pull run skipped: id=%s (gone or disabled)", source_id)
            return

        collector = self._pull_collectors.get(source.type)
        if collector is None:
            logger.warning("pull run skipped: no collector for type=%s", source.type)
            return

        items = await collector.fetch(source)
        logger.info("pull run fetched: link=%s items=%d", source.link, len(items))

        published = await self._publisher.publish_news(items)
        logger.info("pull run published: link=%s items=%d", source.link, published)
