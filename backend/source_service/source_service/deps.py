"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the collector registries and the
concrete repository/publisher, and hands them to application (use cases and the
background aggregators). Everything else depends only on ports.
"""

from common.enums import SourceType
from common.settings import settings

from source_service.application.ports import PullCollector, PushCollector
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

# Registries: SourceType → collector implementation. Injected into the aggregators.
PULL_COLLECTORS: dict[SourceType, PullCollector] = {
    SourceType.RSS: RssCollector(),
    SourceType.WEB: WebCrawlCollector(),
}
PUSH_COLLECTORS: dict[SourceType, PushCollector] = {
    SourceType.TELEGRAM: TelegramCollector(),
}


def get_source_service() -> SourceService:
    """FastAPI use case. SourceRepo opens a session per call, so no request binding."""
    return SourceService(SourceRepo())


def build_rabbit() -> RabbitConnector:
    return RabbitConnector(settings.rabbitmq_url, settings.news_exchange)


def build_scheduler(publisher: RabbitConnector) -> SchedulerService:
    return SchedulerService(publisher, PULL_COLLECTORS, SourceRepo())


def build_subscriptions() -> SubscriptionService:
    return SubscriptionService(PUSH_COLLECTORS, SourceRepo())
