"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the collector registries and the
concrete repository/publisher, and hands them to application (the CRUD use case and
the runtime registry). Everything else depends only on ports.
"""

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings, settings
from common.entities.news import SourceType
from fastapi import Request

from source_service.application.ports.scraping import PageFetcher
from source_service.application.ports.source import (
    NewsPublisher,
    PullCollector,
    PushCollector,
    SourceRegistrar,
)
from source_service.application.services.source import SourceRegistry, SourceService
from source_service.application.services.web import CrawlStages, WebCrawl
from source_service.application.services.web.articles import (
    ArticleFetching,
    ArticleHarvest,
    ArticleJudgement,
    DateResolution,
)
from source_service.application.services.web.hubs import HubDiscovery, ListingClassifier
from source_service.application.services.web.listings import CardCollection
from source_service.infrastructure.collectors.rss import RssCollector
from source_service.infrastructure.collectors.telegram import TelegramCollector
from source_service.infrastructure.collectors.web import WebCrawlCollector
from source_service.infrastructure.crawlers.crawl4ai_fetcher import Crawl4AiPageFetcher
from source_service.infrastructure.crawlers.crawl4ai_pages import Crawl4AiPageCrawler
from source_service.infrastructure.crawlers.feedparser_reader import FeedparserFeedReader
from source_service.infrastructure.crawlers.litellm_client import LiteLlmClient
from source_service.infrastructure.rabbit.connector import RabbitConnector
from source_service.infrastructure.repositories import SourceRepo

logger = get_logger(__name__)


def build_pull_collectors(
    page_fetcher: PageFetcher, page_crawler: Crawl4AiPageCrawler
) -> dict[SourceType, PullCollector]:
    """Pull registry: SourceType → collector. RSS reads feeds over the HTTP `PageFetcher`
    that also backs type auto-detection; WEB drives the browser crawler."""
    rss = RssCollector(FeedparserFeedReader(page_fetcher), page_fetcher)
    return {SourceType.RSS: rss, SourceType.WEB: build_web_collector(page_crawler)}


def crawl_settings() -> WebCrawlSettings:
    """The `web_crawl` group, with the LLM paths switched off when there is no token (or
    `WEB_CRAWL_LLM_ENABLED=false`) — a per-process copy, the singleton is never mutated."""
    runtime = settings.web_crawl
    has_token = bool(settings.llm.llm_token())
    if runtime.llm_enabled and has_token:
        return runtime

    logger.info("web crawl llm disabled: enabled=%s token=%s", runtime.llm_enabled, has_token)
    return runtime.model_copy(update={"llm_enabled": False, "llm_date_fallback": False})


def build_web_collector(page_crawler: Crawl4AiPageCrawler) -> WebCrawlCollector:
    """The crawl is five stages behind one orchestrator; the LLM is one client behind
    two ports, or absent."""
    runtime = crawl_settings()
    llm = LiteLlmClient(settings.llm, runtime) if runtime.llm_enabled else None
    classifier = ListingClassifier(llm, runtime) if llm else None

    stages = CrawlStages(
        hubs=HubDiscovery(page_crawler, classifier, runtime),
        cards=CardCollection(page_crawler, runtime),
        harvest=ArticleHarvest(ArticleFetching(page_crawler, runtime), runtime),
        dates=DateResolution(llm, runtime),
        judgement=ArticleJudgement(runtime),
    )
    return WebCrawlCollector(WebCrawl(stages, SourceRepo()))


def get_source_service(request: Request) -> SourceService:
    """FastAPI use case. SourceRepo opens a session per call, so no request binding.
    The runtime registry and page fetcher are app-lifetime singletons on `app.state`."""
    registrar: SourceRegistrar = request.app.state.registrar
    page_fetcher: PageFetcher = request.app.state.page_fetcher
    return SourceService(SourceRepo(), registrar, page_fetcher)


def build_rabbit() -> RabbitConnector:
    return RabbitConnector(settings.rabbit.rabbitmq_url, settings.rabbit.news_exchange)


def build_page_fetcher() -> Crawl4AiPageFetcher:
    """One HTTP fetcher for the whole service: type auto-detection in `SourceService`
    and every RSS feed/article fetch. Owns a `start`/`stop` lifecycle the caller must
    drive around serving."""
    return Crawl4AiPageFetcher()


def build_page_crawler() -> Crawl4AiPageCrawler:
    """One headless browser for every WEB source pull. Owns a `start`/`close` lifecycle
    the caller must drive around serving."""
    return Crawl4AiPageCrawler(crawl_settings())


def build_telegram_collector(publisher: NewsPublisher) -> TelegramCollector:
    """Push collector; publishes incoming posts through `publisher`. Owns a client
    lifecycle (`start`/`stop`) the caller must drive around serving."""
    return TelegramCollector(
        publisher,
        settings.telegram.api_id,
        settings.telegram.api_hash,
        settings.telegram.session,
    )


def build_registry(
    publisher: RabbitConnector,
    telegram: TelegramCollector,
    page_fetcher: PageFetcher,
    page_crawler: Crawl4AiPageCrawler,
) -> SourceRegistry:
    """The runtime registry: pull scheduling + push subscription behind one registrar."""
    push_collectors: dict[SourceType, PushCollector] = {SourceType.TELEGRAM: telegram}
    pull_collectors = build_pull_collectors(page_fetcher, page_crawler)
    return SourceRegistry(publisher, pull_collectors, push_collectors, SourceRepo())
