"""Read-side use cases over stored news: list everything, dismiss one item."""

import uuid

from domain.core.logging import get_logger
from domain.schemas import News

from news_service.application.ports import NewsRepository

logger = get_logger(__name__)


class NewsService:
    def __init__(self, repo: NewsRepository) -> None:
        self.__repo = repo

    async def list(self, limit: int, offset: int) -> list[News]:
        return await self.__repo.list_all(limit, offset)

    async def dismiss(self, news_id: uuid.UUID) -> News | None:
        """Flag the item as an alert; None when no such news exists."""
        news = await self.__repo.mark_alert(news_id)
        if news is None:
            logger.info("news dismiss skipped: id=%s (not found)", news_id)
            return None

        logger.info("news dismissed: id=%s url=%s", news.id, news.url)
        return news
