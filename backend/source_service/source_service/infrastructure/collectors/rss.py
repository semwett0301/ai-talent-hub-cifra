"""RSS collector (pull) — implements the PullCollector port. STUB: no items yet."""

from common.core.logging import get_logger

from source_service.domain.entities import NewsItem
from source_service.infrastructure.persistence.schemas import Source

logger = get_logger(__name__)


class RssCollector:
    async def fetch(self, source: Source) -> list[NewsItem]:
        # TODO: parse the feed with feedparser; emit entries newer than the cursor.
        logger.info("rss stub fetch: %s", source.link)
        return []
