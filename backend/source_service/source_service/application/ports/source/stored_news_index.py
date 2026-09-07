"""Stored-news port — what a collector needs to know before re-collecting an entry."""

from typing import Protocol


class StoredNewsIndex(Protocol):
    """Answers which of these URLs the shared `news` table already holds.

    Returns the known subset instead of raising, so a lookup failure degrades to
    "nothing is known" — a poll then re-collects rather than dropping news.
    """

    async def list_stored_urls(self, urls: list[str]) -> set[str]: ...
