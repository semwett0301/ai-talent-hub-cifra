"""RssFeedFinder implementation backed by feedsearch-crawler — the one file importing it."""

from collections.abc import Iterable
from typing import Protocol

import aiohttp
from common.core.logging import get_logger
from feedsearch_crawler import search_async

from source_service.application.ports.scraping import RssFeedFinder

# Also probe the usual feed paths (/feed, /rss.xml, ...) when the pages advertise none.
TRY_WELL_KNOWN_PATHS = True
MAX_CRAWL_DEPTH = 5
TOTAL_TIMEOUT_SECONDS = 30.0
RESPECT_ROBOTS = False
RSS_VERSION_PREFIX = "rss"

logger = get_logger(__name__)


class _DiscoveredFeed(Protocol):
    """What is read off feedsearch's `FeedInfo`: where the feed is and which format."""

    @property
    def url(self) -> object: ...

    @property
    def version(self) -> str: ...


def _rss_feed_urls(feeds: Iterable[_DiscoveredFeed]) -> list[str]:
    """RSS feeds only (Atom and JSON Feed are dropped), in the library's score order,
    each URL once."""
    urls: list[str] = []
    for feed in feeds:
        if feed.url is None or not feed.version.startswith(RSS_VERSION_PREFIX):
            continue

        url = str(feed.url)
        if url not in urls:
            urls.append(url)

    return urls


class FeedsearchRssFeedFinder(RssFeedFinder):
    """Crawls the site a few pages deep and returns its RSS feed URLs. Stateless: every
    call opens and closes its own HTTP session, so one instance serves the service."""

    async def find(self, url: str) -> list[str]:
        logger.info("rss feed search started: url=%s", url)
        try:
            feeds = await search_async(
                url,
                try_urls=TRY_WELL_KNOWN_PATHS,
                max_depth=MAX_CRAWL_DEPTH,
                total_timeout=TOTAL_TIMEOUT_SECONDS,
                respect_robots=RESPECT_ROBOTS,
            )
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("rss feed search failed: url=%s (%s)", url, exc)
            return []

        urls = _rss_feed_urls(feeds)
        logger.info("rss feed search finished: url=%s feeds=%d", url, len(urls))
        return urls
