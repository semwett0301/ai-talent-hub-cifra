"""Daily use case that advances tracked bills and records explained changes."""

import uuid
from datetime import UTC, datetime

from common.core.logging import get_logger
from common.schemas import Npa

from npa_service.application.errors import ChangeModelError, NpaSourceError
from npa_service.application.ports import ChangeSummarizer, NpaRepository, NpaSource
from npa_service.domain import ChangeSummary, TrackedUpdate
from npa_service.domain.state import build_tracking_state

logger = get_logger(__name__)
NO_TEXT_CHANGE = "Этап рассмотрения изменился, но текст законопроекта не изменился."


def _has_changed(act: Npa, stage_code: str, document_url: str) -> bool:
    return act.stage_code != stage_code or act.document_url != document_url


class NpaMonitor:
    def __init__(
        self, repo: NpaRepository, source: NpaSource, summarizer: ChangeSummarizer
    ) -> None:
        self.__repo = repo
        self.__source = source
        self.__summarizer = summarizer

    async def check_all(self) -> None:
        acts = await self.__repo.list_tracking()
        logger.info("npa monitoring started: acts=%d", len(acts))
        for act in acts:
            await self.__check_safely(act)
        logger.info("npa monitoring completed: acts=%d", len(acts))

    async def check(self, npa_id: uuid.UUID) -> Npa | None:
        act = await self.__repo.get(npa_id)
        if act is None or not build_tracking_state(act.tracking_status).can_check:
            return act
        return await self.__check(act)

    async def __check_safely(self, act: Npa) -> None:
        try:
            await self.__check(act)
        except (ChangeModelError, NpaSourceError) as error:
            logger.warning("npa monitoring failed: id=%s url=%s error=%s", act.id, act.url, error)

    async def __check(self, act: Npa) -> Npa:
        snapshot = await self.__source.fetch(act.url)
        checked_at = datetime.now(UTC)
        if not _has_changed(act, snapshot.stage_code, snapshot.document_url):
            await self.__repo.mark_checked(act.id, snapshot, checked_at)
            logger.info("npa unchanged: id=%s url=%s stage=%s", act.id, act.url, act.stage_code)
            return act

        change = await self.__summarize(act.text, snapshot.text)
        next_state = build_tracking_state(act.tracking_status).transition(snapshot.is_published)
        updated = await self.__repo.apply_update(
            act.id, TrackedUpdate(snapshot, next_state.status, change)
        )
        logger.info("npa updated: id=%s url=%s stage=%s", act.id, act.url, updated.stage_code)
        return updated

    async def __summarize(self, previous: str, current: str) -> ChangeSummary:
        if previous == current:
            return ChangeSummary(NO_TEXT_CHANGE, ())
        return await self.__summarizer.summarize(previous, current)
