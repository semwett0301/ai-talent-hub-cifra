"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the collector registries and the
concrete repository/publisher, and hands them to application (use cases and the
background aggregators). Everything else depends only on ports.
"""

from common.enums import SourceType
from common.settings import settings

from source_service.application.ports import NewsPublisher, PullCollector, PushCollector
from source_service.application.services import (
    SchedulerService,
    SourceService,
    SubscriptionService,
)
from source_service.infrastructure.collectors import (
    RssCollector,
    TelegramCollector,
    WebCrawlCollector,
)
from source_service.infrastructure.rabbit.connector import RabbitConnector
from source_service.infrastructure.repositories import SourceRepo

# Pull registry: SourceType → collector. Push collectors need the publisher, so
# they are built per-run (see `build_telegram_collector`), not as a constant.
PULL_COLLECTORS: dict[SourceType, PullCollector] = {
    SourceType.RSS: RssCollector(),
    SourceType.WEB: WebCrawlCollector(),
}


def get_source_service() -> SourceService:
    """FastAPI use case. SourceRepo opens a session per call, so no request binding."""
    return SourceService(SourceRepo())


def build_rabbit() -> RabbitConnector:
    return RabbitConnector(settings.rabbitmq_url, settings.news_exchange)


def build_scheduler(publisher: RabbitConnector) -> SchedulerService:
    return SchedulerService(publisher, PULL_COLLECTORS, SourceRepo())


def build_telegram_collector(publisher: NewsPublisher) -> TelegramCollector:
    """Push collector; publishes incoming posts through `publisher`. Owns a client
    lifecycle (`start`/`stop`) the caller must drive around serving."""
    return TelegramCollector(
        publisher,
        settings.telegram_api_id,
        settings.telegram_api_hash,
        settings.telegram_session,
    )


def build_subscriptions(telegram: TelegramCollector) -> SubscriptionService:
    push_collectors: dict[SourceType, PushCollector] = {SourceType.TELEGRAM: telegram}
    return SubscriptionService(push_collectors, SourceRepo())
