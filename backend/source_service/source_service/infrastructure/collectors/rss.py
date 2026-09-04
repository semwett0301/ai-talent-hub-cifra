"""RSS collector (pull) — implements the PullCollector port. STUB: no items yet."""

from domain.core.logging import get_logger
from domain.entities.news import NewsDTO
from domain.schemas import Source

from source_service.application.ports import PullCollector

logger = get_logger(__name__)


class RssCollector(PullCollector):
    async def fetch(self, source: Source) -> list[NewsDTO]:
        # TODO: parse the feed with feedparser; emit entries newer than the cursor.
        logger.info("rss stub fetch: %s", source.rss_link)
        return []
