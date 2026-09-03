"""RabbitConnector — implements the NewsPublisher port over the `news` exchange.

`publish_news` maps `NewsItem` → `common.dto.NewsDTO` and publishes it.
"""

import aio_pika
from common.core.logging import get_logger
from common.dto import NewsDTO, routing_key
from common.enums import SourceType

from source_service.domain.entities import NewsItem

logger = get_logger(__name__)


class RabbitConnector:
    def __init__(self, url: str, exchange_name: str) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        logger.info("rabbit connected, exchange=%s", self._exchange_name)

    async def publish_news(
        self, source_id: int, source_type: SourceType, items: list[NewsItem]
    ) -> int:
        if self._exchange is None:
            logger.warning("rabbit not connected; dropping %d items", len(items))
            return 0
        key = routing_key(source_type)
        for item in items:
            event = NewsDTO(
                source_id=source_id,
                source_type=source_type,
                url=item.url,
                text=item.text,
                published_at=item.published_at,
                raw=item.raw,
            )
            message = aio_pika.Message(
                event.model_dump_json().encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self._exchange.publish(message, routing_key=key)
        return len(items)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
