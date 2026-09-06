"""NewsFeed — the read side of stored news: page through it, open one, hide and unhide."""

import uuid

from common.core.logging import get_logger
from common.schemas import News

from news_service.application.dto.news import NewsQuery
from news_service.application.ports import NewsRepository

logger = get_logger(__name__)


class NewsFeed:
    def __init__(self, repo: NewsRepository) -> None:
        self.__repo = repo

    async def list(self, query: NewsQuery) -> tuple[list[News], int]:
        """The requested page and the total matching the same filters."""
        items = await self.__repo.list_page(query)
        total = await self.__repo.count(query)
        return items, total

    async def get(self, news_id: uuid.UUID) -> News | None:
        return await self.__repo.get(news_id)

    async def dismiss(self, news_id: uuid.UUID) -> News | None:
        """Hide the item from the feed; None when no such news exists."""
        news = await self.__repo.mark_dismissed(news_id)
        if news is None:
            logger.info("news dismiss skipped: id=%s (not found)", news_id)
            return None

        await self.__repo.commit()
        logger.info("news dismissed: id=%s url=%s", news.id, news.url)
        return news

    async def restore(self, news_id: uuid.UUID) -> News | None:
        """Bring a hidden item back; None when no such news exists."""
        news = await self.__repo.mark_restored(news_id)
        if news is None:
            logger.info("news restore skipped: id=%s (not found)", news_id)
            return None

        await self.__repo.commit()
        logger.info("news restored: id=%s url=%s", news.id, news.url)
        return news
