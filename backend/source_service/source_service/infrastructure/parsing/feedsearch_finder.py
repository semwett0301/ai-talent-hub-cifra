"""RssFeedFinder implementation backed by feedsearch-crawler — the one file importing it."""

from collections.abc import Iterable
from typing import Protocol

import aiohttp
from common.core.logging import get_logger
from common.core.settings import RssDiscoverySettings
from feedsearch_crawler import search_async

from source_service.application.ports.scraping import RssFeedFinder

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
    """Crawls the site as deep as `settings` allow and returns its RSS feed URLs.
    Stateless: every call opens and closes its own HTTP session, so one instance serves
    the service."""

    def __init__(self, settings: RssDiscoverySettings) -> None:
        self.__settings = settings

    async def find(self, url: str) -> list[str]:
        logger.info("rss feed search started: url=%s", url)
        try:
            feeds = await search_async(
                url,
                try_urls=self.__settings.try_well_known_paths,
                max_depth=self.__settings.max_depth,
                total_timeout=self.__settings.timeout_seconds,
                respect_robots=self.__settings.respect_robots,
            )
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("rss feed search failed: url=%s (%s)", url, exc)
            return []

        urls = _rss_feed_urls(feeds)
        logger.info("rss feed search finished: url=%s feeds=%d", url, len(urls))
        return urls
