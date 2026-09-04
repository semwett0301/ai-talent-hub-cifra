"""Pull aggregator — schedules a periodic fetch→publish per pull source.

Loads enabled pull sources on startup and runs each collector on its interval.
Collaborators (publisher, collectors, source loaders) are injected from `deps`.
Live re-scheduling on CRUD is a TODO; for now sources are picked up at startup.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.core.logging import get_logger
from common.enums import SourceType

from source_service.application.ports import NewsPublisher, PullCollector, SourceRepository

logger = get_logger(__name__)

DEFAULT_INTERVAL_SECONDS = 300


class SchedulerService:
    def __init__(
        self,
        publisher: NewsPublisher,
        pull_collectors: dict[SourceType, PullCollector],
        repository: SourceRepository,
    ) -> None:
        self._publisher = publisher
        self._pull_collectors = pull_collectors
        self._repository = repository
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    async def load(self) -> None:
        for source in await self._repository.list_enabled():
            if source.type in self._pull_collectors:
                self._add(source.id, source.poll_interval_seconds)

    def _add(self, source_id: int, interval: int | None) -> None:
        self._scheduler.add_job(
            self._run,
            "interval",
            seconds=interval or DEFAULT_INTERVAL_SECONDS,
            args=[source_id],
            id=f"src-{source_id}",
            replace_existing=True,
        )

    async def _run(self, source_id: int) -> None:
        source = await self._repository.get(source_id)
        if source is None or not source.is_enabled:
            return
        collector = self._pull_collectors.get(source.type)
        if collector is None:
            return
        items = await collector.fetch(source)
        await self._publisher.publish_news(source.id, source.type, items)
