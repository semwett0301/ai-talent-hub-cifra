"""Register a State Duma URL and persist its initial snapshot."""

from common.core.logging import get_logger
from common.entities.npa import NpaTrackingStatus
from common.schemas import Npa

from npa_service.application.ports import NpaRepository, NpaSource
from npa_service.domain.state import build_tracking_state

logger = get_logger(__name__)


class NpaRegistration:
    def __init__(self, repo: NpaRepository, source: NpaSource) -> None:
        self.__repo = repo
        self.__source = source

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
