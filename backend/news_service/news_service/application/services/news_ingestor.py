"""Batch ingest use case — stores one batch of consumed news through the repository port.

Implements `NewsBatchHandler`: the shared bus consumer hands over a batch, this writes
it in one transaction. Duplicates by `url` — repeats inside the batch as much as urls
already stored — are skipped by the DB (`ON CONFLICT DO NOTHING`), so no dedupe happens
here. Storage failures propagate as `NewsStoreError` (a `BatchStoreError`) so the
consumer nacks the batch (requeue or drop, per its config).
"""

from domain.core.logging import get_logger
from domain.entities.news import NewsDTO

from news_service.application.ports import NewsBatchHandler, NewsRepository

logger = get_logger(__name__)


class NewsIngestor(NewsBatchHandler):
    def __init__(self, repo: NewsRepository) -> None:
        self.__repo = repo

    async def handle_batch(self, items: list[NewsDTO]) -> int:
        inserted = await self.__repo.add_many(items)

        logger.info(
            "news batch stored: received=%d inserted=%d skipped=%d",
            len(items),
            inserted,
            len(items) - inserted,
        )
        return inserted
