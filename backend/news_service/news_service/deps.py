"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it scopes the unit of work (a DB session per HTTP
request, one per consumed batch), builds the repository on it and hands the application
use cases to their callers. Everything else depends only on ports.
"""

from collections.abc import AsyncIterator

from common.core.db import async_session_factory
from common.core.rabbit import BatchConsumerConfig, RabbitBatchConsumer
from common.core.settings import settings
from common.entities.news import ROUTING_PREFIX, NewsDTO
from fastapi import Depends

from news_service.application.ports import NewsBatchHandler
from news_service.application.services import NewsFeed, NewsIngestor, NpaEscalation
from news_service.infrastructure.gateways import HttpNpaGateway
from news_service.infrastructure.repositories import NewsRepo

# Every per-type routing key (`news.raw.telegram`, `news.raw.rss`, …).
NEWS_BINDING_KEY = f"{ROUTING_PREFIX}.#"


async def get_news_repo() -> AsyncIterator[NewsRepo]:
    """One session per request: closed (rolled back, unless committed) when the response is out."""
    async with async_session_factory() as session:
        yield NewsRepo(session)


def get_news_feed(repo: NewsRepo = Depends(get_news_repo)) -> NewsFeed:
    return NewsFeed(repo)


def get_npa_escalation(repo: NewsRepo = Depends(get_news_repo)) -> NpaEscalation:
    """Flag + register in npa_service (over HTTP) as one unit — the repo's session spans both."""
    return NpaEscalation(repo, HttpNpaGateway(settings.npa.npa_service_url))


class BatchScope(NewsBatchHandler):
    """A session per consumed batch — the consumer's counterpart of `get_news_repo`.

    The consumer lives for the whole process, so it cannot hold one session; each batch
    gets a fresh one, closed when the batch is stored or refused (rolled back)."""

    async def handle_batch(self, items: list[NewsDTO]) -> int:
        async with async_session_factory() as session:
            return await NewsIngestor(NewsRepo(session)).handle_batch(items)


def build_consumer() -> RabbitBatchConsumer[NewsDTO]:
    """The bus entry point; owns a `start`/`stop` lifecycle the caller drives around
    serving. Parses deliveries into `NewsDTO` and feeds batches to `NewsIngestor`."""
    config = BatchConsumerConfig(
        url=settings.rabbit.rabbitmq_url,
        exchange_name=settings.rabbit.news_exchange,
        queue_name=settings.news.queue,
        binding_key=NEWS_BINDING_KEY,
        batch_size=settings.news.batch_size,
        batch_interval_seconds=settings.news.batch_interval_seconds,
        requeue_on_store_error=settings.news.requeue_on_store_error,
    )
    return RabbitBatchConsumer(config, BatchScope(), NewsDTO)
