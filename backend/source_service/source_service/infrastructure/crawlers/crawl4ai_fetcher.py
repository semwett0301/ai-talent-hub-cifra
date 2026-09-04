"""PageFetcher implementation backed by crawl4ai — the one file importing it."""

import aiohttp
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from domain.core.logging import get_logger

from source_service.application.ports import PageFetcher

logger = get_logger(__name__)


class Crawl4AiPageFetcher(PageFetcher):
    """Lightweight HTTP-only fetch (no browser/Playwright): feed XML, article HTML,
    or a page's `<head>` for an RSS `<link>` tag."""

    def __init__(self) -> None:
        self.__crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())

    async def start(self) -> None:
        await self.__crawler.start()
        logger.info("page fetcher started")

    async def close(self) -> None:
        await self.__crawler.close()
        logger.info("page fetcher closed")

    async def fetch(self, url: str) -> str | None:
        # crawl4ai narrates every fetch to stdout unless told not to; we log it ourselves.
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        try:
            result = await self.__crawler.arun(url, config=run_config)
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("crawl failed: %s (%s)", url, exc)
            return None

        if not result.success:
            logger.warning("crawl unsuccessful: %s (%s)", url, result.error_message)
            return None

        logger.info("page fetched: %s (%d bytes)", url, len(result.html or ""))
        return result.html
