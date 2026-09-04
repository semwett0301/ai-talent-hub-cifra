"""Telegram collector (push) — implements the PushCollector port. STUB: no-op."""

from common.core.logging import get_logger

from source_service.domain.schemas import Source

logger = get_logger(__name__)


class TelegramCollector:
    async def subscribe(self, source: Source) -> None:
        # TODO: aiogram — start watching the channel; a decorated handler will
        # publish incoming posts as NewsItem.
        logger.info("telegram stub subscribe: %s", source.link)

    async def unsubscribe(self, source: Source) -> None:
        logger.info("telegram stub unsubscribe: %s", source.link)
