"""NpaEscalation — turn a news item into a legislative act: flag it + register, atomically."""

import uuid

from common.core.logging import get_logger
from common.entities.npa import NpaDTO
from common.schemas import News
from pydantic import HttpUrl

from news_service.application.ports import NewsRepository, NpaGateway

logger = get_logger(__name__)


def _act_from_news(news: News) -> NpaDTO:
    """The act as the news item itself describes it — what the client would have sent."""
    return NpaDTO(
        url=HttpUrl(news.url), title=news.title, text=news.text, published_at=news.published_at
    )


class NpaEscalation:
    def __init__(self, repo: NewsRepository, npa_gateway: NpaGateway) -> None:
        self.__repo = repo
        self.__npa_gateway = npa_gateway

    async def escalate(self, news_id: uuid.UUID, act: NpaDTO | None) -> News | None:
        """Flag the item as an alert and register the act in `npa_service` as one unit.

        The `is_alert` flip is staged, the remote create runs, and only a confirmed act
        commits it — a failed call (any `NpaGatewayError`) propagates before `commit()`,
        so the unit of work ends uncommitted and the flip is rolled back. Without `act`,
        the act is built from the news item. None when no such news exists (nothing is sent)."""
        news = await self.__repo.mark_alert(news_id)
        if news is None:
            logger.info("news escalation skipped: id=%s (not found)", news_id)
            return None

        npa_id = await self.__npa_gateway.create(act or _act_from_news(news))
        await self.__repo.commit()

        logger.info("news escalated: id=%s url=%s npa_id=%s", news.id, news.url, npa_id)
        return news
