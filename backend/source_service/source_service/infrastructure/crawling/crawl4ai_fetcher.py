"""PageFetcher implementation backed by crawl4ai — the one file importing it."""

import aiohttp
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from domain.core.logging import get_logger

from source_service.application.ports import PageFetcher

logger = get_logger(__name__)


class Crawl4AiPageFetcher(PageFetcher):
    """Lightweight HTTP-only fetch (no browser/Playwright) — enough to read a
    page's `<head>` for an RSS `<link>` tag."""

    def __init__(self) -> None:
        self.__crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())

    async def start(self) -> None:
        await self.__crawler.start()

    async def close(self) -> None:
        await self.__crawler.close()

    async def fetch(self, url: str) -> str | None:
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        try:
            result = await self.__crawler.arun(url, config=run_config)
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("crawl failed: %s (%s)", url, exc)
            return None

        if not result.success:
            logger.warning("crawl unsuccessful: %s (%s)", url, result.error_message)
            return None

        return result.html
