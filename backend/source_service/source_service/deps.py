"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the collector registries and the
concrete repository/publisher, and hands them to application (use cases and the
background aggregators). Everything else depends only on ports.
"""

from common.core.session import async_session_factory, get_session
from common.enums import SourceType
from common.settings import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from source_service.infrastructure.persistence.repositories.source_repo import SourceRepo
from source_service.infrastructure.persistence.schemas import Source
from source_service.infrastructure.rabbit.connector import RabbitConnector

# Registries: SourceType → collector implementation. Injected into the aggregators.
PULL_COLLECTORS: dict[SourceType, PullCollector] = {
    SourceType.RSS: RssCollector(),
    SourceType.WEB: WebCrawlCollector(),
}
PUSH_COLLECTORS: dict[SourceType, PushCollector] = {
    SourceType.TELEGRAM: TelegramCollector(),
}


async def get_source_service(session: AsyncSession = Depends(get_session)) -> SourceService:
    """FastAPI request-scoped use case, backed by a session-bound repository."""
    return SourceService(SourceRepo(session))


async def _load_enabled_sources() -> list[Source]:
    async with async_session_factory() as session:
        return await SourceRepo(session).list_enabled()


async def _get_source(source_id: int) -> Source | None:
    async with async_session_factory() as session:
        return await SourceRepo(session).get(source_id)


def build_rabbit() -> RabbitConnector:
    return RabbitConnector(settings.rabbitmq_url, settings.news_exchange)


def build_scheduler(publisher: RabbitConnector) -> SchedulerService:
    return SchedulerService(publisher, PULL_COLLECTORS, _load_enabled_sources, _get_source)


def build_subscriptions() -> SubscriptionService:
    return SubscriptionService(PUSH_COLLECTORS, _load_enabled_sources)
