"""FeedReader implementation backed by feedparser — the one file importing it.

The feed body is fetched through the `PageFetcher` port (bounded, async, never raises)
and only the parsing is handed to feedparser. Letting feedparser fetch the URL itself
would block on urllib with no timeout. Parsing stays inline: it takes tens of ms even
on a 200-entry feed, once per pull, so a worker thread would buy nothing.
"""

from calendar import timegm
from datetime import UTC, datetime
from html.parser import HTMLParser
from time import struct_time
from typing import Any

import feedparser
from domain.core.logging import get_logger

from source_service.application.ports import FeedEntry, FeedReader, PageFetcher

logger = get_logger(__name__)


class _TextOnlyParser(HTMLParser):
    """Strips markup from a feed summary, keeping just its text."""

    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)


def _strip_html(markup: str) -> str:
    parser = _TextOnlyParser()
    parser.feed(markup)
    return " ".join("".join(parser.chunks).split())


def _published_at(raw_entry: dict[str, Any]) -> datetime | None:
    parsed_time: struct_time | None = raw_entry.get("published_parsed") or raw_entry.get(
        "updated_parsed"
    )
    if parsed_time is None:
        return None

    return datetime.fromtimestamp(timegm(parsed_time), tz=UTC)


def _to_entry(raw_entry: dict[str, Any]) -> FeedEntry:
    return FeedEntry(
        url=raw_entry["link"],
        title=_strip_html(raw_entry.get("title", "")),
        summary=_strip_html(raw_entry.get("summary", "")),
        published_at=_published_at(raw_entry),
    )


class FeedparserFeedReader(FeedReader):
    def __init__(self, page_fetcher: PageFetcher) -> None:
        self.__page_fetcher = page_fetcher

    async def read(self, feed_url: str) -> list[FeedEntry]:
        body = await self.__page_fetcher.fetch(feed_url)
        if body is None:
            return []

        parsed = feedparser.parse(body)
        if parsed.bozo:
            logger.warning("feed parsed with errors: feed=%s (%s)", feed_url, parsed.bozo_exception)

        entries = [_to_entry(raw_entry) for raw_entry in parsed.entries if raw_entry.get("link")]
        logger.info("feed fetched: feed=%s entries=%d", feed_url, len(entries))
        return entries
