"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the concrete repository and the
shared RabbitMQ batch consumer, and hands the application use cases to them.
Everything else depends only on ports.
"""

from common.core.rabbit import BatchConsumerConfig, RabbitBatchConsumer
from common.core.settings import settings
from common.entities.news import ROUTING_PREFIX, NewsDTO

from news_service.application.services import NewsFeed, NewsIngestor
from news_service.infrastructure.repositories import NewsRepo

# Every per-type routing key (`news.raw.telegram`, `news.raw.rss`, …).
NEWS_BINDING_KEY = f"{ROUTING_PREFIX}.#"


def get_news_feed() -> NewsFeed:
    """FastAPI use case. NewsRepo opens a session per call, so no request binding."""
    return NewsFeed(NewsRepo())


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
    return RabbitBatchConsumer(config, NewsIngestor(NewsRepo()), NewsDTO)
