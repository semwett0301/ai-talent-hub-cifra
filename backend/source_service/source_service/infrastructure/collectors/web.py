"""`WebCrawlCollector` — the pull collector for ordinary web sites (no RSS)."""

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import Source

from source_service.application.ports.source import PullCollector
from source_service.application.services.scraping import WebCrawl
from source_service.domain import Site

logger = get_logger(__name__)


class WebCrawlCollector(PullCollector):
    """Turns a `Source` row into a `Site`, runs the crawl, emits the accepted articles."""

    def __init__(self, crawl: WebCrawl) -> None:
        self.__crawl = crawl

    async def fetch(self, source: Source) -> list[NewsDTO]:
        site = Site(url=source.link, name=source.name)
        logger.info("web crawl started: source=%s", source.link)
        # Boundary with the scheduler: a broken site must not take the registry down.
        try:
            articles = await self.__crawl.run(site)
        except Exception:
            logger.exception("web crawl failed: source=%s", source.link)
            return []

        news = [article.to_news_dto(source) for article in articles]
        logger.info("web crawl collected: source=%s items=%d", source.link, len(news))
        return news
