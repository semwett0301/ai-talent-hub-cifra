"""RSS collector (pull) — implements the PullCollector port.

Polls every feed in `source.rss_links` through the `FeedReader` port, fetches each
entry's page through the `PageFetcher` port and extracts its full text with
`parse.extract_article` before mapping it to a `NewsDTO`. A site's feeds overlap, so an
entry seen in two feeds is collected once (first feed wins).

A feed lists its whole window on every poll (200-300 entries is normal), so entries the
shared `news` table already holds are dropped through `StoredNewsFilter` before any page
is fetched — otherwise each poll re-crawls the entire feed. The collector keeps no state
of its own: the DB is the record of what was collected, keyed by `NewsDTO.url` (the
entry's canonical link), the same key downstream dedupes on.
"""

import asyncio

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import RssLink, Source

from source_service.application.parse import ExtractedArticle, extract_article
from source_service.application.ports.scraping import FeedEntry, FeedReader, PageFetcher
from source_service.application.ports.source import PullCollector
from source_service.application.services.dedup import StoredNewsFilter

MAX_CONCURRENT_EXTRACTIONS = 4

logger = get_logger(__name__)


def _to_news_dto(source: Source, entry: FeedEntry, article: ExtractedArticle | None) -> NewsDTO:
    # Full article text when extraction worked; the feed's own summary otherwise.
    text = article.text if article is not None else entry.summary
    # A titleless entry falls back to its text, the same last resort the Telegram collector uses.
    title = (article.title if article is not None and article.title else entry.title) or text
    published_at = entry.published_at or (article.published_at if article is not None else None)

    return NewsDTO.for_source(
        source,
        url=entry.url,
        title=title,
        text=text,
        excerpt=entry.summary or None,
        published_at=published_at,
        updated_at=entry.updated_at,
        source_tags=entry.tags,
    )


class RssCollector(PullCollector):
    def __init__(
        self,
        feed_reader: FeedReader,
        page_fetcher: PageFetcher,
        stored_news: StoredNewsFilter,
    ) -> None:
        self.__feed_reader = feed_reader
        self.__page_fetcher = page_fetcher
        self.__stored_news = stored_news

    async def fetch(self, source: Source) -> list[NewsDTO]:
        if not source.rss_links:
            logger.warning("rss fetch skipped: id=%s link=%s (no feeds)", source.id, source.link)
            return []

        entries = await self.__read_feeds(source.rss_links)
        fresh = await self.__stored_news.unstored(source.link, entries)
        if not fresh:
            return []

        return await self.__collect(source, fresh)

    async def __read_feeds(self, feeds: list[RssLink]) -> list[FeedEntry]:
        """Every feed's entries, an entry URL kept once — the feed that listed it first."""
        seen_urls: set[str] = set()
        entries: list[FeedEntry] = []

        for feed in feeds:
            fresh = [
                entry
                for entry in await self.__feed_reader.read(feed.url)
                if entry.url not in seen_urls
            ]

            seen_urls.update(entry.url for entry in fresh)
            entries.extend(fresh)

        return entries

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
