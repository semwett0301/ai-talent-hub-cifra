"""Crawler port — the crawl4ai capability application needs, implemented in infrastructure."""

from typing import Protocol


class PageFetcher(Protocol):
    """Fetches a URL's page content for downstream rule-based inspection.

    Returns `None` on failure (timeout, DNS, unreachable site, ...) instead of
    raising, so callers treat "couldn't fetch" as one uniform signal.
    """

    async def fetch(self, url: str) -> str | None: ...
