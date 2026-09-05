"""BatchHandler — the inward-facing port the shared consumer hands each batch to."""

from typing import Protocol

from pydantic import BaseModel


class BatchHandler[T: BaseModel](Protocol):
    """Persists one batch of parsed messages; returns the number newly stored.

    Raises `BatchStoreError` (`common.core.errors`) when the batch could not be written,
    so the consumer nacks the messages (requeue or drop, per config) instead of
    acknowledging them."""

    async def handle_batch(self, items: list[T]) -> int: ...
