"""NewsBatchHandler — the shared `BatchHandler` port narrowed to news, implemented in application."""

from typing import Protocol

from common.core.rabbit import BatchHandler
from common.entities.news import NewsDTO


class NewsBatchHandler(BatchHandler[NewsDTO], Protocol):
    """Persists one batch of consumed news; returns the number newly stored.

    Raises `BatchStoreError` when the batch could not be fully processed,
    so the shared consumer hands the messages back to the broker instead of acking."""
