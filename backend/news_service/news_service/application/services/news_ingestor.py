"""Batch ingest use case — stores one batch of consumed news through the repository port.

Implements `NewsBatchHandler`: the shared bus consumer hands over a batch, this
dedupes it by `url` within the batch (the DB skips urls it already holds) and writes it
in one transaction. Storage failures propagate as `NewsStoreError` (a `BatchStoreError`)
so the consumer requeues the batch.
"""

from domain.core.logging import get_logger
from domain.entities.news import NewsDTO

from news_service.application.ports import NewsBatchHandler, NewsRepository

logger = get_logger(__name__)


def _dedupe_by_url(items: list[NewsDTO]) -> list[NewsDTO]:
    """Keep the first occurrence of each url, preserving arrival order."""
    first_by_url: dict[str, NewsDTO] = {}
    for item in items:
        first_by_url.setdefault(item.url, item)

    return list(first_by_url.values())


class NewsIngestor(NewsBatchHandler):
    def __init__(self, repo: NewsRepository) -> None:
        self.__repo = repo

    async def handle_batch(self, items: list[NewsDTO]) -> int:
        unique = _dedupe_by_url(items)

        inserted = await self.__repo.add_many(unique)

        logger.info(
            "news batch stored: received=%d unique=%d inserted=%d duplicates=%d",
            len(items),
            len(unique),
            inserted,
            len(unique) - inserted,
        )
        return inserted
