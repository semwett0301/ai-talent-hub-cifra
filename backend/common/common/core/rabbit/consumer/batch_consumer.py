"""RabbitBatchConsumer — consumes a topic exchange in batches, feeding a `BatchHandler`.

AMQP delivers one message at a time, so the batching lives here. The consume callback
does nothing but drop each delivery into an inbox (`asyncio.Queue`); a single runner
task takes them out: it waits for the first delivery, then keeps collecting until the
batch is full or `batch_interval_seconds` have passed since that first delivery —
whichever first — and hands the parsed batch to the handler in one call (one DB
transaction). `prefetch_count` = batch size caps how many unacknowledged deliveries the
broker pushes, so the inbox never holds more than one batch.

Acks go out only after the handler returns; if it raises `BatchStoreError` the run is
nacked — back onto the queue when `config.requeue_on_store_error` is set (the runner
then backs off one interval), or dropped otherwise. At-least-once delivery + an
idempotent handler (e.g. a unique key in the DB) = no loss, no duplicates.

One task owns the buffer, so there is no shared mutable state to lock: the callback
and the runner meet only at the inbox.
"""

import asyncio

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue, AbstractRobustConnection
from pydantic import BaseModel

from common.core.errors import BatchStoreError
from common.core.logging import get_logger
from common.core.rabbit.consumer.message_batch import MessageBatch
from common.core.rabbit.model import BatchConsumerConfig, BatchHandler

logger = get_logger(__name__)
CAUSE_SEPARATOR = " <- "


def _describe(error: BaseException) -> str:
    """The failure and its `raise ... from` chain, so a requeue names its root cause."""
    parts: list[str] = []
    current: BaseException | None = error
    while current is not None:
        parts.append(
            f"{type(current).__name__}: {str(current).splitlines()[0] if str(current) else ''}"
        )
        current = current.__cause__
    return CAUSE_SEPARATOR.join(parts)


class RabbitBatchConsumer[T: BaseModel]:
    def __init__(
        self, config: BatchConsumerConfig, handler: BatchHandler[T], model: type[T]
    ) -> None:
        self.__config = config
        self.__handler = handler
        self.__model = model

        self.__connection: AbstractRobustConnection | None = None
        self.__queue: AbstractQueue | None = None
        self.__consumer_tag: str | None = None

        self.__inbox: asyncio.Queue[AbstractIncomingMessage] = asyncio.Queue()
        self.__pending: list[AbstractIncomingMessage] = []
        self.__runner: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self.__connection = await aio_pika.connect_robust(self.__config.url)
        channel = await self.__connection.channel()
        await channel.set_qos(prefetch_count=self.__config.batch_size)

        exchange = await channel.declare_exchange(
            self.__config.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        self.__queue = await channel.declare_queue(self.__config.queue_name, durable=True)
        await self.__queue.bind(exchange, routing_key=self.__config.binding_key)

        # Deliveries only land in the inbox here; the runner is the sole reader.
        self.__consumer_tag = await self.__queue.consume(self.__inbox.put)
        self.__runner = asyncio.create_task(self.__run())

        logger.info(
            "rabbit consumer started: queue=%s binding=%s model=%s batch_size=%d interval=%.0fs",
            self.__config.queue_name,
            self.__config.binding_key,
            self.__model.__name__,
            self.__config.batch_size,
            self.__config.batch_interval_seconds,
        )

    async def stop(self) -> None:
        # Stop new deliveries first, then let the runner drain what it already has.
        if self.__queue is not None and self.__consumer_tag is not None:
            await self.__queue.cancel(self.__consumer_tag)

        if self.__runner is not None:
            self.__runner.cancel()
            await asyncio.gather(self.__runner, return_exceptions=True)

        if self.__connection is not None:
            await self.__connection.close()

        logger.info("rabbit consumer stopped: queue=%s", self.__config.queue_name)

    async def __run(self) -> None:
        try:
            while True:
                await self.__collect()
                await self.__store_pending()
        except asyncio.CancelledError:
            await self.__drain()
            raise

    async def __collect(self) -> None:
        """Wait for the first delivery, then take more until the batch is full or the
        interval since that first delivery elapsed — whichever first."""
        self.__pending.append(await self.__inbox.get())

        deadline = asyncio.get_running_loop().time() + self.__config.batch_interval_seconds
        while len(self.__pending) < self.__config.batch_size:
            try:
                async with asyncio.timeout_at(deadline):
                    self.__pending.append(await self.__inbox.get())
            except TimeoutError:
                return

    async def __store_pending(self) -> None:
        messages, self.__pending = self.__pending, []

        is_stored = await self.__flush(messages)
        if not is_stored:
            # The run is settled (requeued or dropped); back off so a dead DB doesn't spin us.
            await asyncio.sleep(self.__config.batch_interval_seconds)

    async def __drain(self) -> None:
        """On shutdown, store what was collected plus anything delivered meanwhile."""
        while not self.__inbox.empty():
            self.__pending.append(self.__inbox.get_nowait())

        messages, self.__pending = self.__pending, []
        await self.__flush(messages)

    async def __flush(self, messages: list[AbstractIncomingMessage]) -> bool:
        """Store one run and settle it with the broker; False when the handler failed
        (the run is already nacked), so the caller can back off."""
        if not messages:
            return True

        batch = MessageBatch(messages, self.__model)
        await batch.reject_invalid()
        if not batch.items:
            return True

        try:
            await self.__handler.handle_batch(batch.items)
        except BatchStoreError as error:
            await self.__settle_failed(batch, error)
            return False

        await batch.ack()
        return True

    async def __settle_failed(self, batch: MessageBatch[T], error: BatchStoreError) -> None:
        """Hand a batch the handler could not store back to the broker: requeued for
        another attempt, or dropped when `requeue_on_store_error` is off."""
        if self.__config.requeue_on_store_error:
            await batch.requeue()
            outcome = "requeued"
        else:
            await batch.drop()
            outcome = "dropped"

        logger.warning(
            "batch %s: queue=%s items=%d (store failed: %s)",
            outcome,
            self.__config.queue_name,
            len(batch.items),
            _describe(error),
        )
