"""Web crawl collector (pull) — implements the PullCollector port. STUB: no items yet."""

from common.core.logging import get_logger

from source_service.domain.entities import NewsItem
from source_service.infrastructure.persistence.schemas import Source

logger = get_logger(__name__)


class WebCrawlCollector:
    async def fetch(self, source: Source) -> list[NewsItem]:
        # TODO: crawl4ai opens the site, follows links; an LLM decides relevance.
        logger.info("web stub fetch: %s", source.link)
        return []
