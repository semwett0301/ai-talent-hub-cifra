"""RSS collector (pull) — implements the PullCollector port.

Polls every feed in `source.rss_links` through the `FeedReader` port, fetches each
entry's page through the `PageFetcher` port and extracts its full text with
`parse.extract_article` before mapping it to a `NewsDTO`. A site's feeds overlap, so an
entry seen in two feeds is collected once (first feed wins). Stateless by design: each
pull emits the feeds' current entries and forgets them — downstream dedupes on
`NewsDTO.url` (the entry's canonical link), which is why that field is the key.
"""

import asyncio
from dataclasses import dataclass

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import RssLink, Source

from source_service.application.parse import ExtractedArticle, extract_article
from source_service.application.ports.scraping import FeedEntry, FeedReader, PageFetcher
from source_service.application.ports.source import PullCollector

MAX_CONCURRENT_EXTRACTIONS = 4

logger = get_logger(__name__)


@dataclass(frozen=True)
class _FeedItem:
    """One feed entry together with the feed it came from."""

    entry: FeedEntry
    feed_url: str


def _to_news_dto(source: Source, item: _FeedItem, article: ExtractedArticle | None) -> NewsDTO:
    entry = item.entry
    # Full article text when extraction worked; the feed's own summary otherwise.
    text = article.text if article is not None else entry.summary
    title = article.title if article is not None and article.title else entry.title
    published_at = entry.published_at or (article.published_at if article is not None else None)

    return NewsDTO.for_source(
        source.link,
        source.type,
        source.reliability,
        source_id=source.id,
        url=entry.url,
        text=text,
        published_at=published_at,
        raw={"title": title, "summary": entry.summary, "feed_url": item.feed_url},
    )


class RssCollector(PullCollector):
    def __init__(self, feed_reader: FeedReader, page_fetcher: PageFetcher) -> None:
        self.__feed_reader = feed_reader
        self.__page_fetcher = page_fetcher

    async def fetch(self, source: Source) -> list[NewsDTO]:
        if not source.rss_links:
            logger.warning("rss fetch skipped: id=%s link=%s (no feeds)", source.id, source.link)
            return []

        items = await self.__read_feeds(source.rss_links)
        if not items:
            return []

        return await self.__collect(source, items)

    async def __read_feeds(self, feeds: list[RssLink]) -> list[_FeedItem]:
        """Every feed's entries, an entry URL kept once — the feed that listed it first."""
        seen_urls: set[str] = set()
        items: list[_FeedItem] = []

        for feed in feeds:
            entries = await self.__feed_reader.read(feed.url)
            fresh = [entry for entry in entries if entry.url not in seen_urls]

            seen_urls.update(entry.url for entry in fresh)
            items.extend(_FeedItem(entry, feed.url) for entry in fresh)

        return items

    async def __collect(self, source: Source, items: list[_FeedItem]) -> list[NewsDTO]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTIONS)

        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(self.__collect_one(source, item, semaphore)) for item in items
            ]

        return [task.result() for task in tasks]

    async def __collect_one(
        self, source: Source, item: _FeedItem, semaphore: asyncio.Semaphore
    ) -> NewsDTO:
        async with semaphore:
            article = await self.__extract(item.entry.url)

        return _to_news_dto(source, item, article)

    async def __extract(self, url: str) -> ExtractedArticle | None:
        html = await self.__page_fetcher.fetch(url)
        if html is None:
            return None

        # Extraction is blocking lxml work (~0.2s/article) — keep it off the event loop.
        article = await asyncio.to_thread(extract_article, html, url)
        if article is None:
            logger.warning("article extraction empty: url=%s", url)
            return None

        logger.info("article extracted: url=%s chars=%d", url, len(article.text))
        return article
