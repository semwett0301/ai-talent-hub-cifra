"""Register a State Duma URL and persist its initial snapshot."""

import asyncio
import uuid

from common.core.logging import get_logger
from common.entities.npa import NpaTrackingStatus
from common.schemas import Npa

from npa_service.application.errors import ChangeModelError
from npa_service.application.ports import InitialSummarizer, NpaRepository, NpaSource
from npa_service.domain import BillSnapshot
from npa_service.domain.state import build_tracking_state

logger = get_logger(__name__)
INITIAL_SUMMARY_ATTEMPTS = 3
INITIAL_SUMMARY_RETRY_SECONDS = 1


class NpaRegistration:
    def __init__(
        self, repo: NpaRepository, source: NpaSource, initial_summarizer: InitialSummarizer
    ) -> None:
        self.__repo = repo
        self.__source = source
        self.__initial_summarizer = initial_summarizer

    async def register(self, url: str) -> Npa:
        snapshot = await self.__source.fetch(url)
        initial = build_tracking_state(NpaTrackingStatus.TRACKING)
        status = initial.transition(snapshot.is_published).status
        stored = await self.__repo.add(snapshot, status)

        logger.info(
            "npa registered: id=%s url=%s stage=%s status=%s",
            stored.id,
            stored.url,
            stored.stage_code,
            stored.tracking_status.value,
        )
        return stored

    async def generate_initial_summary(self, npa_id: uuid.UUID) -> None:
        """Build the overview after responding to the registration request."""
        act = await self.__repo.get(npa_id)
        if act is None:
            return
        snapshot = BillSnapshot(
            url=act.url,
            bill_number=act.bill_number or "",
            title=act.title,
            stage=act.stage or "",
            stage_code=act.stage_code or "",
            text=act.text,
            document_url=act.document_url or act.url,
            updated_at=act.source_updated_at or act.created_at,
            published_at=act.published_at,
        )
        for attempt in range(1, INITIAL_SUMMARY_ATTEMPTS + 1):
            try:
                summary = await self.__initial_summarizer.summarize(snapshot)
                await self.__repo.set_initial_summary(npa_id, summary)
                logger.info("npa initial summary completed: id=%s attempt=%d", npa_id, attempt)
                return
            except ChangeModelError as error:
                logger.warning(
                    "npa initial summary failed: id=%s attempt=%d/%d error=%s",
                    npa_id,
                    attempt,
                    INITIAL_SUMMARY_ATTEMPTS,
                    error,
                )
                if attempt < INITIAL_SUMMARY_ATTEMPTS:
                    await asyncio.sleep(INITIAL_SUMMARY_RETRY_SECONDS * attempt)
        await self.__repo.mark_initial_summary_failed(npa_id)
