"""MessageBatch — one flush's worth of deliveries: parse them, then settle them as a whole."""

from collections.abc import Awaitable

from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import AMQPError
from aiormq.exceptions import ChannelInvalidStateError
from pydantic import BaseModel, ValidationError

from domain.core.logging import get_logger

logger = get_logger(__name__)

# Settling can fail only when the channel was reset underneath us (robust reconnect);
# the broker then redelivers the run, which an idempotent handler absorbs harmlessly.
SETTLE_ERRORS = (AMQPError, ChannelInvalidStateError)


class MessageBatch[T: BaseModel]:
    """Splits deliveries into parsed `model` instances and unparseable ones.

    Delivery tags grow monotonically on a channel, so acking/nacking the **last** valid
    message with `multiple=True` settles every earlier unacked delivery of this run in
    one frame — no per-message round trips.
    """

    def __init__(self, messages: list[AbstractIncomingMessage], model: type[T]) -> None:
        self.__model = model
        self.__valid: list[AbstractIncomingMessage] = []
        self.__invalid: list[AbstractIncomingMessage] = []
        self.__items: list[T] = []

        for message in messages:
            self.__parse(message)

    @property
    def items(self) -> list[T]:
        return self.__items

    async def reject_invalid(self) -> None:
        """Drop unparseable messages without requeue — they would never store."""
        for message in self.__invalid:
            await self.__settle(message.reject(requeue=False), "reject")

        if self.__invalid:
            logger.warning(
                "messages dropped: model=%s count=%d (invalid payload)",
                self.__model.__name__,
                len(self.__invalid),
            )

    async def ack(self) -> None:
        if not self.__valid:
            return

        await self.__settle(self.__valid[-1].ack(multiple=True), "ack")

    async def requeue(self) -> None:
        if not self.__valid:
            return

        await self.__settle(self.__valid[-1].nack(multiple=True, requeue=True), "nack")

    async def drop(self) -> None:
        """Nack without requeue — the run is gone (or dead-lettered if the queue has a DLX)."""
        if not self.__valid:
            return

        await self.__settle(self.__valid[-1].nack(multiple=True, requeue=False), "drop")

    def __parse(self, message: AbstractIncomingMessage) -> None:
        try:
            item = self.__model.model_validate_json(message.body)
        except ValidationError as error:
            logger.warning(
                "message rejected: model=%s key=%s errors=%d",
                self.__model.__name__,
                message.routing_key,
                error.error_count(),
            )
            self.__invalid.append(message)
            return

        self.__valid.append(message)
        self.__items.append(item)

    async def __settle(self, operation: Awaitable[None], name: str) -> None:
        try:
            await operation
        except SETTLE_ERRORS as error:
            logger.warning(
                "rabbit %s failed: messages=%d error=%s (channel reset; broker redelivers)",
                name,
                len(self.__valid),
                error,
            )
