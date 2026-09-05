"""RSS collector (pull) — implements the PullCollector port.

Polls `source.rss_link` through the `FeedReader` port, fetches every entry's page
through the `PageFetcher` port and extracts its full text with `parse.extract_article`
before mapping it to a `NewsDTO`. Stateless by design: each pull emits the feed's
current entries and forgets them — downstream dedupes on `NewsDTO.url` (the entry's
canonical link), which is why that field is the key.
"""

import asyncio

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import Source

from source_service.application.parse import ExtractedArticle, extract_article
from source_service.application.ports.scraping import FeedEntry, FeedReader, PageFetcher
from source_service.application.ports.source import PullCollector

MAX_CONCURRENT_EXTRACTIONS = 4

logger = get_logger(__name__)


def _to_news_dto(source: Source, entry: FeedEntry, article: ExtractedArticle | None) -> NewsDTO:
    # Full article text when extraction worked; the feed's own summary otherwise.
    text = article.text if article is not None else entry.summary
    title = article.title if article is not None and article.title else entry.title
    published_at = entry.published_at or (article.published_at if article is not None else None)

    return NewsDTO.for_source(
        source.link,
        source.type,
        source.reliability,
        url=entry.url,
        text=text,
        published_at=published_at,
        raw={"title": title, "summary": entry.summary, "feed_url": source.rss_link},
    )


class RssCollector(PullCollector):
    def __init__(self, feed_reader: FeedReader, page_fetcher: PageFetcher) -> None:
        self.__feed_reader = feed_reader
        self.__page_fetcher = page_fetcher

    async def fetch(self, source: Source) -> list[NewsDTO]:
        feed_url = source.rss_link
        if feed_url is None:
            logger.warning("rss fetch skipped: id=%s link=%s (no rss_link)", source.id, source.link)
            return []

        entries = await self.__feed_reader.read(feed_url)
        if not entries:
            return []

        return await self.__collect(source, entries)

    async def __collect(self, source: Source, entries: list[FeedEntry]) -> list[NewsDTO]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTIONS)

        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(self.__collect_one(source, entry, semaphore)) for entry in entries
            ]

        return [task.result() for task in tasks]

    async def __collect_one(
        self, source: Source, entry: FeedEntry, semaphore: asyncio.Semaphore
    ) -> NewsDTO:
        async with semaphore:
            article = await self.__extract(entry.url)

        return _to_news_dto(source, entry, article)

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
