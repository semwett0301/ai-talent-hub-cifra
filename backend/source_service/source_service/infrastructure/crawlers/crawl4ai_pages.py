"""`Crawl4AiPageCrawler` — the `PageCrawler` port on Crawl4AI's headless browser."""

from typing import Any

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from source_service.application.ports.scraping import FetchedPage, PageCrawler, PageLink

logger = get_logger(__name__)

WORD_COUNT_THRESHOLD = 10
EXCLUDED_TAGS = ["script", "style", "noscript", "svg", "form"]
ARTICLE_EXCLUDED_TAGS = [*EXCLUDED_TAGS, "nav", "footer", "aside"]


def to_page(result: Any) -> FetchedPage:
    """Free a page from Crawl4AI's result type; article runs carry `fit_markdown`."""
    markdown = getattr(result, "markdown", None)
    if not isinstance(markdown, str):
        markdown = getattr(markdown, "fit_markdown", None) or getattr(markdown, "raw_markdown", "")

    metadata = result.metadata if isinstance(getattr(result, "metadata", None), dict) else {}
    links = getattr(result, "links", None)
    internal = links.get("internal", []) if isinstance(links, dict) else []
    return FetchedPage(
        url=str(result.url),
        final_url=str(getattr(result, "redirected_url", None) or result.url),
        html=getattr(result, "html", None) or getattr(result, "cleaned_html", None) or "",
        markdown=markdown or "",
        title=str(metadata.get("title") or metadata.get("og:title") or "").strip() or None,
        links=tuple(
            PageLink(str(link.get("href") or ""), str(link.get("text") or link.get("title") or ""))
            for link in internal
        ),
        metadata=dict(metadata),
    )


class Crawl4AiPageCrawler(PageCrawler):
    """One headless Chromium for the whole service; `start`/`close` are driven by `main`'s
    lifespan like the other infra clients, and concurrent pulls share it."""

    def __init__(self, settings: WebCrawlSettings) -> None:
        self.__settings = settings
        self.__crawler: AsyncWebCrawler | None = None

    async def start(self) -> None:
        self.__crawler = AsyncWebCrawler(
            config=BrowserConfig(headless=True, text_mode=True, verbose=False)
        )
        await self.__crawler.start()
        logger.info("browser crawler started")

    async def close(self) -> None:
        if self.__crawler is not None:
            await self.__crawler.close()
            self.__crawler = None
            logger.info("browser crawler closed")

    async def crawl_page(self, url: str) -> FetchedPage | None:
        pages = await self.__run_many([url], self.__config())
        return pages[0] if pages else None

    async def crawl_pages(self, urls: list[str]) -> list[FetchedPage]:
        return await self.__run_many(urls, self.__config())

    async def crawl_articles(self, urls: list[str]) -> list[FetchedPage]:
        # Keep the page HTML intact: the date cascade needs the complete DOM.
        return await self.__run_many(urls, self.__config(article=True))

    def __browser(self) -> AsyncWebCrawler:
        if self.__crawler is None:
            raise RuntimeError("Crawl4AiPageCrawler is used before start()")
        return self.__crawler

    def __config(self, *, article: bool = False) -> CrawlerRunConfig:
        generator = None
        if article:
            generator = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=self.__settings.pruning_threshold,
                    threshold_type="fixed",
                    min_word_threshold=self.__settings.pruning_min_words,
                )
            )
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=generator,
            excluded_tags=ARTICLE_EXCLUDED_TAGS if article else EXCLUDED_TAGS,
            exclude_external_links=True,
            check_robots_txt=self.__settings.check_robots_txt,
            user_agent=self.__settings.user_agent,
            page_timeout=self.__settings.page_timeout_ms,
            wait_until="domcontentloaded",
            word_count_threshold=WORD_COUNT_THRESHOLD,
            semaphore_count=self.__settings.crawl_concurrency,
        )

    async def __run_many(self, urls: list[str], config: CrawlerRunConfig) -> list[FetchedPage]:
        if not urls:
            return []
        # Boundary with the browser: any failure here is "these pages are unavailable".
        try:
            results = await self.__browser().arun_many(urls, config=config)
        except Exception:
            logger.exception("crawl batch failed: urls=%d", len(urls))
            return []

        pages = [to_page(result) for result in results if getattr(result, "success", False)]
        logger.info("pages crawled: requested=%d ok=%d", len(urls), len(pages))
        return pages
