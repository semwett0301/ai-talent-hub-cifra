"""Feed port — reads an RSS/Atom feed into plain entries; implemented in infrastructure.

`FeedEntry` is the port's return shape: what a feed item carries before the article
itself is fetched. `url` is the entry's canonical link and becomes `NewsDTO.url`, the
key downstream dedupes on.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class FeedEntry:
    url: str
    title: str
    summary: str
    published_at: datetime | None
    updated_at: datetime | None = None
    tags: list[str] = field(default_factory=list)


class FeedReader(Protocol):
    """Downloads and parses one feed; returns `[]` (never raises) when it can't."""

    async def read(self, feed_url: str) -> list[FeedEntry]: ...
