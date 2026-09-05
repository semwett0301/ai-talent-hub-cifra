"""RabbitConnector — implements the NewsPublisher port over the `news` exchange.

`publish_news` publishes each `common.entities.news.NewsDTO` with its per-type routing key.
"""

import aio_pika
from common.core.logging import get_logger
from common.entities.news import NewsDTO, routing_key

from source_service.application.ports.source import NewsPublisher

logger = get_logger(__name__)


class RabbitConnector(NewsPublisher):
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

    async def publish_news(self, items: list[NewsDTO]) -> int:
        exchange = self._exchange
        if exchange is None:
            logger.warning("rabbit not connected; dropping %d items", len(items))
            return 0

        if not items:
            return 0

        for item in items:
            key = routing_key(item.source_type)
            await exchange.publish(self.__to_message(item), routing_key=key)
            logger.debug("news item published: key=%s url=%s", key, item.url)

        logger.info("news published: exchange=%s items=%d", self._exchange_name, len(items))
        return len(items)

    async def close(self) -> None:
        if self._connection is None:
            return

        await self._connection.close()
        logger.info("rabbit connection closed")

    @staticmethod
    def __to_message(item: NewsDTO) -> aio_pika.Message:
        return aio_pika.Message(
            item.model_dump_json().encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
