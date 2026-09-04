"""RabbitNewsConsumer — consumes the `news` exchange in batches, feeding `NewsBatchHandler`.

AMQP delivers one message at a time, so the batching lives here. `prefetch_count` =
batch size caps how many unacknowledged messages the broker pushes; deliveries are
buffered **unacked** and flushed — one handler call, one DB transaction — when the
buffer is full or the interval elapses, whichever first. Acks go out only after the
batch is stored; if storing fails the run is nacked back to the queue and the next
attempt waits one interval. At-least-once delivery + the unique `url` in the DB = no
loss, no duplicates.
"""

import asyncio
from contextlib import suppress

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue, AbstractRobustConnection
from domain.core.logging import get_logger
from domain.entities.news import ROUTING_PREFIX

from news_service.application.errors import NewsStoreError
from news_service.application.ports import NewsBatchHandler
from news_service.infrastructure.rabbit.batch import MessageBatch
from news_service.infrastructure.rabbit.config import RabbitConsumerConfig

# Every per-type routing key (`news.raw.telegram`, `news.raw.rss`, …).
BINDING_KEY = f"{ROUTING_PREFIX}.#"

logger = get_logger(__name__)


class RabbitNewsConsumer:
    def __init__(self, config: RabbitConsumerConfig, handler: NewsBatchHandler) -> None:
        self.__config = config
        self.__handler = handler

        self.__connection: AbstractRobustConnection | None = None
        self.__queue: AbstractQueue | None = None
        self.__consumer_tag: str | None = None

        self.__pending: list[AbstractIncomingMessage] = []
        self.__batch_full = asyncio.Event()
        self.__flush_lock = asyncio.Lock()
        self.__flusher: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self.__connection = await aio_pika.connect_robust(self.__config.url)
        channel = await self.__connection.channel()
        await channel.set_qos(prefetch_count=self.__config.batch_size)

        exchange = await channel.declare_exchange(
            self.__config.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        self.__queue = await channel.declare_queue(self.__config.queue_name, durable=True)
        await self.__queue.bind(exchange, routing_key=BINDING_KEY)

        self.__consumer_tag = await self.__queue.consume(self.__on_message)
        self.__flusher = asyncio.create_task(self.__flush_forever())

        logger.info(
            "rabbit consumer started: queue=%s binding=%s batch_size=%d interval=%.0fs",
            self.__config.queue_name,
            BINDING_KEY,
            self.__config.batch_size,
            self.__config.batch_interval_seconds,
        )

    async def stop(self) -> None:
        if self.__queue is not None and self.__consumer_tag is not None:
            await self.__queue.cancel(self.__consumer_tag)

        if self.__flusher is not None:
            self.__flusher.cancel()
            await asyncio.gather(self.__flusher, return_exceptions=True)

        # Store what is still buffered before letting go of the channel.
        with suppress(NewsStoreError):
            await self.__flush()

        if self.__connection is not None:
            await self.__connection.close()

        logger.info("rabbit consumer stopped: queue=%s", self.__config.queue_name)

    async def __on_message(self, message: AbstractIncomingMessage) -> None:
        self.__pending.append(message)

        if len(self.__pending) >= self.__config.batch_size:
            self.__batch_full.set()

    async def __flush_forever(self) -> None:
        while True:
            await self.__wait_for_batch()

            try:
                await self.__flush()
            except NewsStoreError:
                # The run is back on the queue; back off so a dead DB doesn't spin us.
                await asyncio.sleep(self.__config.batch_interval_seconds)

    async def __wait_for_batch(self) -> None:
        """Returns when the buffer is full or the interval elapsed, whichever first."""
        try:
            await asyncio.wait_for(
                self.__batch_full.wait(), timeout=self.__config.batch_interval_seconds
            )
        except TimeoutError:
            return

    async def __flush(self) -> None:
        async with self.__flush_lock:
            messages, self.__pending = self.__pending, []
            self.__batch_full.clear()
            if not messages:
                return

            batch = MessageBatch(messages)
            await batch.reject_invalid()
            if not batch.items:
                return

            try:
                await self.__handler.handle_batch(batch.items)
            except NewsStoreError:
                await batch.requeue()
                logger.warning("news batch requeued: items=%d (store failed)", len(batch.items))
                raise

            await batch.ack()
