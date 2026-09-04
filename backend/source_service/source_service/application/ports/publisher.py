"""Publisher port — the message-bus contract, implemented in infrastructure."""

import uuid
from typing import Protocol

from common.enums import SourceType

from source_service.domain.entities import NewsItem


class NewsPublisher(Protocol):
    """Publishes collected news items to the bus; returns the count published."""

    async def publish_news(
        self, source_id: uuid.UUID, source_type: SourceType, items: list[NewsItem]
    ) -> int: ...
