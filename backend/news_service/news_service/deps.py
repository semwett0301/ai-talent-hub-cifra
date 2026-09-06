"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the concrete repository and the
shared RabbitMQ batch consumer, and hands the application use cases to them.
Everything else depends only on ports.
"""

from common.core.rabbit import BatchConsumerConfig, RabbitBatchConsumer
from common.core.settings import settings
from common.entities.news import ROUTING_PREFIX, NewsDTO

from news_service.application.services import (
    NewsDeduplicator,
    NewsFeed,
    NewsIngestor,
    NewsRanker,
    NpaEscalation,
)
from news_service.infrastructure.dedup import (
    OpenRouterEventModels,
    SentenceTransformerSummaryEmbedder,
)
from news_service.infrastructure.gateways import HttpNpaGateway
from news_service.infrastructure.ranking import OpenRouterRankingModels, load_company_profile
from news_service.infrastructure.repositories import (
    NewsRepo,
    SqlDedupRepository,
    SqlRankingRepository,
)

# Every per-type routing key (`news.raw.telegram`, `news.raw.rss`, …).
NEWS_BINDING_KEY = f"{ROUTING_PREFIX}.#"


def get_news_feed() -> NewsFeed:
    """FastAPI use case. NewsRepo opens a session per call, so no request binding."""
    return NewsFeed(NewsRepo())


def get_npa_escalation() -> NpaEscalation:
    """FastAPI use case: dismiss + register in npa_service (over HTTP) as one unit."""
    return NpaEscalation(NewsRepo(), HttpNpaGateway(settings.npa.npa_service_url))


def build_consumer() -> RabbitBatchConsumer[NewsDTO]:
    """The bus entry point; owns a `start`/`stop` lifecycle the caller drives around
    serving. Parses deliveries into `NewsDTO` and feeds batches to `NewsIngestor`."""
    dedup_repository = SqlDedupRepository()
    embedder = SentenceTransformerSummaryEmbedder(
        settings.news_dedup.embedding_model,
        settings.news_dedup.embedding_batch_size,
    )
    event_models = _event_models()
    stages = _build_pipeline(dedup_repository, event_models, embedder)
    handler = NewsIngestor(dedup_repository, event_models, embedder, stages)
    return RabbitBatchConsumer(_consumer_config(), handler, NewsDTO)


def _consumer_config() -> BatchConsumerConfig:
    return BatchConsumerConfig(
        url=settings.rabbit.rabbitmq_url,
        exchange_name=settings.rabbit.news_exchange,
        queue_name=settings.news.queue,
        binding_key=NEWS_BINDING_KEY,
        batch_size=settings.news.batch_size,
        batch_interval_seconds=settings.news.batch_interval_seconds,
        requeue_on_store_error=settings.news.requeue_on_store_error,
    )


def _event_models() -> OpenRouterEventModels:
    return OpenRouterEventModels(
        settings.llm.openrouter_api_key,
        settings.llm.openrouter_base_url,
        settings.news_dedup,
    )


def _build_pipeline(
    dedup_repository: SqlDedupRepository,
    event_models: OpenRouterEventModels,
    embedder: SentenceTransformerSummaryEmbedder,
) -> tuple[NewsDeduplicator, NewsRanker]:
    deduplicator = NewsDeduplicator(dedup_repository, event_models, settings.news_dedup)
    ranking_models = OpenRouterRankingModels(
        settings.llm.openrouter_api_key,
        settings.llm.openrouter_base_url,
        settings.news_ranking,
    )
    ranker = NewsRanker(
        SqlRankingRepository(),
        ranking_models,
        embedder,
        load_company_profile(),
    )
    return deduplicator, ranker
