"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the collector registries and the
concrete repository/publisher, and hands them to application (the CRUD use case and
the runtime registry). Everything else depends only on ports.
"""

from domain.core.settings import settings
from domain.entities.news import SourceType
from fastapi import Request

from source_service.application.ports import (
    NewsPublisher,
    PageFetcher,
    PullCollector,
    PushCollector,
    SourceRegistrar,
)
from source_service.application.services import SourceRegistry, SourceService
from source_service.infrastructure.collectors import (
    RssCollector,
    TelegramCollector,
    WebCrawlCollector,
)
from source_service.infrastructure.crawlers import Crawl4AiPageFetcher, FeedparserFeedReader
from source_service.infrastructure.rabbit.connector import RabbitConnector
from source_service.infrastructure.repositories import SourceRepo


def build_pull_collectors(page_fetcher: PageFetcher) -> dict[SourceType, PullCollector]:
    """Pull registry: SourceType → collector. The RSS collector reads feeds and fetches
    articles over the same `PageFetcher` that backs type auto-detection."""
    rss = RssCollector(FeedparserFeedReader(page_fetcher), page_fetcher)
    return {SourceType.RSS: rss, SourceType.WEB: WebCrawlCollector()}


def get_source_service(request: Request) -> SourceService:
    """FastAPI use case. SourceRepo opens a session per call, so no request binding.
    The runtime registry and page fetcher are app-lifetime singletons on `app.state`."""
    registrar: SourceRegistrar = request.app.state.registrar
    page_fetcher: PageFetcher = request.app.state.page_fetcher
    return SourceService(SourceRepo(), registrar, page_fetcher)


def build_rabbit() -> RabbitConnector:
    return RabbitConnector(settings.rabbitmq_url, settings.news_exchange)


def build_page_fetcher() -> Crawl4AiPageFetcher:
    """One HTTP fetcher for the whole service: type auto-detection in `SourceService`
    and every RSS feed/article fetch. Owns a `start`/`stop` lifecycle the caller must
    drive around serving."""
    return Crawl4AiPageFetcher()


def build_telegram_collector(publisher: NewsPublisher) -> TelegramCollector:
    """Push collector; publishes incoming posts through `publisher`. Owns a client
    lifecycle (`start`/`stop`) the caller must drive around serving."""
    return TelegramCollector(
        publisher,
        settings.telegram_api_id,
        settings.telegram_api_hash,
        settings.telegram_session,
    )


def build_registry(
    publisher: RabbitConnector, telegram: TelegramCollector, page_fetcher: PageFetcher
) -> SourceRegistry:
    """The runtime registry: pull scheduling + push subscription behind one registrar."""
    push_collectors: dict[SourceType, PushCollector] = {SourceType.TELEGRAM: telegram}
    pull_collectors = build_pull_collectors(page_fetcher)
    return SourceRegistry(publisher, pull_collectors, push_collectors, SourceRepo())
