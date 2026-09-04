"""Web crawl collector (pull) — implements the PullCollector port. STUB: no items yet."""

from common.core.logging import get_logger

from source_service.application.ports import PullCollector
from source_service.domain.schemas import NewsItem, Source

logger = get_logger(__name__)


class WebCrawlCollector(PullCollector):
    async def fetch(self, source: Source) -> list[NewsItem]:
        # TODO: crawl4ai opens the site, follows links; an LLM decides relevance.
        logger.info("web stub fetch: %s", source.link)
        return []
