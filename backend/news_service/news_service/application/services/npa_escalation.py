"""NpaEscalation — turn a news alert into a legislative act: dismiss + register, atomically."""

import uuid

from domain.core.logging import get_logger
from domain.entities.npa import NpaDTO
from domain.schemas import News

from news_service.application.ports import NewsRepository, NpaGateway

logger = get_logger(__name__)


class NpaEscalation:
    def __init__(self, repo: NewsRepository, npa_gateway: NpaGateway) -> None:
        self.__repo = repo
        self.__npa_gateway = npa_gateway

    async def escalate(self, news_id: uuid.UUID, act: NpaDTO) -> News | None:
        """Dismiss the alert and register the act in `npa_service` as one unit.

        The `is_alert` flip is staged first, the remote create runs inside the same
        transaction, and only a confirmed act commits it — a failed call (any
        `NpaGatewayError`) propagates and the flip is rolled back. None when no such
        news exists (nothing is sent)."""
        async with self.__repo.begin() as transaction:
            news = await transaction.mark_alert(news_id)
            if news is None:
                logger.info("news escalation skipped: id=%s (not found)", news_id)
                return None

            npa_id = await self.__npa_gateway.create(act)
            await transaction.commit()

        logger.info("news escalated: id=%s url=%s npa_id=%s", news.id, news.url, npa_id)
        return news
