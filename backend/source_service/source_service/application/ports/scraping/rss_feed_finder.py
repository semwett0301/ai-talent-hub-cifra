"""Feed-discovery port — every RSS feed a site offers, implemented in infrastructure."""

from typing import Protocol


class RssFeedFinder(Protocol):
    """Finds the RSS feed URLs behind a site address: advertised in its pages or served
    at well-known paths. Never raises — an unreachable site or a site without feeds
    is `[]`, so callers treat "no feed" as one uniform signal."""

    async def find(self, url: str) -> list[str]: ...
