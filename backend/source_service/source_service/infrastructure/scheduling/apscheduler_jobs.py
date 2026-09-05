"""`ApSchedulerJobs` — the `JobScheduler` port on APScheduler's asyncio scheduler."""

import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.core.logging import get_logger

from source_service.application.ports.source import JobScheduler, PullRun

logger = get_logger(__name__)

JOB_ID_PREFIX = "src-"


class ApSchedulerJobs(JobScheduler):
    """Owns the scheduler and its `start`/`shutdown` lifecycle, which the caller drives
    around serving. Source ids are turned into job ids here — no caller sees one."""

    def __init__(self) -> None:
        self.__scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self.__scheduler.start()
        logger.info("job scheduler started")

    def shutdown(self) -> None:
        self.__scheduler.shutdown(wait=False)
        logger.info("job scheduler stopped")

    def schedule(self, source_id: uuid.UUID, seconds: int, run: PullRun) -> None:
        self.__scheduler.add_job(
            run,
            "interval",
            seconds=seconds,
            args=[source_id],
            id=self.__job_id(source_id),
            replace_existing=True,
        )

    def unschedule(self, source_id: uuid.UUID) -> None:
        if self.__scheduler.get_job(self.__job_id(source_id)) is None:
            return
        self.__scheduler.remove_job(self.__job_id(source_id))

    def __job_id(self, source_id: uuid.UUID) -> str:
        return f"{JOB_ID_PREFIX}{source_id}"
