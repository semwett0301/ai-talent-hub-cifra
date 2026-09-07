"""Batch ingest: checkpoint summaries, then run ordered post-summary stages."""

import uuid

from common.core.logging import get_logger
from common.core.rabbit import BatchHandler
from common.entities.news import NewsDTO

from news_service.application.errors import (
    EventModelError,
    NewsProcessingError,
    RankingModelError,
    SummaryEmbeddingError,
)
from news_service.application.ports import DedupRepository, EventModels, SummaryEmbedder
from news_service.application.services.news_ingestor.pipeline_stage import NewsPipelineStage
from news_service.domain.event_summary import NewsTarget, PreparedNews

logger = get_logger(__name__)


class NewsIngestor(BatchHandler[NewsDTO]):
    def __init__(
        self,
        repository: DedupRepository,
        models: EventModels,
        embedder: SummaryEmbedder,
        stages: tuple[NewsPipelineStage, ...],
    ) -> None:
        self.__repository = repository
        self.__models = models
        self.__embedder = embedder
        self.__stages = stages

    async def handle_batch(self, items: list[NewsDTO]) -> int:
        unique_items = _unique_by_url(items)
        states = await self.__repository.list_states([item.url for item in unique_items])
        targets = [
            NewsTarget(states[item.url].news_id if item.url in states else uuid.uuid4(), item)
            for item in unique_items
            if item.url not in states or not states[item.url].has_summary
        ]
        try:
            await self.__summarize_and_save(targets)
            urls = [item.url for item in unique_items]
            await self.__embed_and_save(urls)
            for stage in self.__stages:
                await stage.process(urls)
        except (EventModelError, RankingModelError, SummaryEmbeddingError) as error:
            raise NewsProcessingError(
                f"news batch processing failed: items={len(items)}"
            ) from error

        inserted = sum(item.url not in states for item in unique_items)

        logger.info(
            "news batch stored: received=%d inserted=%d skipped=%d",
            len(items),
            inserted,
            len(items) - inserted,
        )
        return inserted

    async def __summarize_and_save(self, targets: list[NewsTarget]) -> None:
        if not targets:
            return

        summaries = await self.__models.summarize(targets)
        items_by_id = {target.news_id: target.news for target in targets}
        prepared = [PreparedNews(items_by_id[summary.news_id], summary) for summary in summaries]
        await self.__repository.save_summaries(prepared)
        logger.info("news summaries stored: items=%d", len(prepared))

    async def __embed_and_save(self, urls: list[str]) -> None:
        summaries = await self.__repository.list_unembedded(urls)
        if not summaries:
            return
        vectors = self.__embedder.embed([summary.text for summary in summaries])
        if len(vectors) != len(summaries):
            raise SummaryEmbeddingError("embedding count does not match summary count")
        embedded = [
            summary.with_embedding(vector)
            for summary, vector in zip(summaries, vectors, strict=True)
        ]
        await self.__repository.save_embeddings(embedded)


def _unique_by_url(items: list[NewsDTO]) -> list[NewsDTO]:
    urls: set[str] = set()
    unique: list[NewsDTO] = []
    for item in items:
        if item.url in urls:
            continue
        urls.add(item.url)
        unique.append(item)
    return unique
