"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the concrete repository and the
RabbitMQ consumer, and hands the application use cases to them. Everything else
depends only on ports.
"""

from domain.core.settings import settings

from news_service.application.services import NewsIngestor, NewsService
from news_service.infrastructure.rabbit import RabbitConsumerConfig, RabbitNewsConsumer
from news_service.infrastructure.repositories import NewsRepo


def get_news_service() -> NewsService:
    """FastAPI use case. NewsRepo opens a session per call, so no request binding."""
    return NewsService(NewsRepo())


def build_consumer() -> RabbitNewsConsumer:
    """The bus entry point; owns a `start`/`stop` lifecycle the caller drives around
    serving. Feeds batches to `NewsIngestor` through the `NewsBatchHandler` port."""
    config = RabbitConsumerConfig(
        url=settings.rabbitmq_url,
        exchange_name=settings.news_exchange,
        queue_name=settings.news_queue,
        batch_size=settings.news_batch_size,
        batch_interval_seconds=settings.news_batch_interval_seconds,
    )
    return RabbitNewsConsumer(config, NewsIngestor(NewsRepo()))
