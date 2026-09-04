"""Ingest port — what the bus consumer hands a batch of news to, implemented in application."""

from typing import Protocol

from domain.entities.news import NewsDTO


class NewsBatchHandler(Protocol):
    """Persists one batch of consumed news; returns the number newly stored.

    Raises `NewsStoreError` when the batch could not be written, so the caller can
    hand the messages back to the broker instead of acknowledging them."""

    async def handle_batch(self, items: list[NewsDTO]) -> int: ...
