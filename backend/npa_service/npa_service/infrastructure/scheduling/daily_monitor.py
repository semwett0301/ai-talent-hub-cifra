"""APScheduler adapter for one coalesced daily NPA monitoring run."""

from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.core.logging import get_logger

logger = get_logger(__name__)
RunMonitor = Callable[[], Awaitable[None]]
JOB_ID = "npa-daily-monitor"


class DailyMonitor:
    def __init__(self, interval_seconds: int, run: RunMonitor) -> None:
        self.__interval_seconds = interval_seconds
        self.__run = run
        self.__scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self.__scheduler.add_job(
            self.__run,
            "interval",
            seconds=self.__interval_seconds,
            id=JOB_ID,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self.__scheduler.start()
        logger.info("npa scheduler started: interval_seconds=%s", self.__interval_seconds)

    def shutdown(self) -> None:
        self.__scheduler.shutdown(wait=False)
        logger.info("npa scheduler stopped")
