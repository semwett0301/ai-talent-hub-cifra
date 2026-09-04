"""Web crawl collector (pull) — implements the PullCollector port. STUB: no items yet."""

from domain.core.logging import get_logger
from domain.entities.news import NewsDTO
from domain.schemas import Source

from source_service.application.ports import PullCollector

logger = get_logger(__name__)


class WebCrawlCollector(PullCollector):
    async def fetch(self, source: Source) -> list[NewsDTO]:
        # TODO: crawl4ai opens the site, follows links; an LLM decides relevance.
        logger.info("web stub fetch: %s", source.link)
        return []
