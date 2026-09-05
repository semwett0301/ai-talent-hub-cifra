"""`Crawl4AiPageCrawler` — the `PageCrawler` port on Crawl4AI's headless browser."""

import math
from collections.abc import AsyncIterator
from typing import Any

from common.core.logging import get_logger
from common.core.settings import LlmSettings, WebCrawlSettings
from crawl4ai import (
    AdaptiveConfig,
    AdaptiveCrawler,
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from source_service.application.ports.scraping import FetchedPage, PageCrawler, PageLink

logger = get_logger(__name__)

NEWS_KEYWORDS = [
    "news",
    "press",
    "newsroom",
    "media",
    "article",
    "publication",
    "blog",
    "release",
    "event",
    "новости",
    "пресс",
    "медиа",
    "статья",
    "публикация",
    "релиз",
    "события",
]
KEYWORD_WEIGHT = 0.7
WORD_COUNT_THRESHOLD = 10
EXCLUDED_TAGS = ["script", "style", "noscript", "svg", "form"]
ARTICLE_EXCLUDED_TAGS = [*EXCLUDED_TAGS, "nav", "footer", "aside"]
LLM_ADAPTIVE_STRATEGIES = {"embedding", "llm"}


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

    def __init__(self, settings: WebCrawlSettings, llm: LlmSettings) -> None:
        self.__settings = settings
        self.__llm = llm
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

    async def adaptive_discover(self, seed_url: str) -> list[FetchedPage]:
        adaptive = AdaptiveCrawler(self.__browser(), config=self.__adaptive_config())
        try:
            state = await adaptive.digest(start_url=seed_url, query=self.__settings.discovery_query)
        except Exception:
            logger.exception("adaptive crawl failed: seed=%s", seed_url)
            return []
        return [to_page(result) for result in (getattr(state, "knowledge_base", None) or [])]

    async def best_first_discover(self, hub_url: str) -> AsyncIterator[FetchedPage]:
        strategy = BestFirstCrawlingStrategy(
            max_depth=self.__settings.best_first_depth,
            include_external=False,
            url_scorer=KeywordRelevanceScorer(keywords=NEWS_KEYWORDS, weight=KEYWORD_WEIGHT),
            max_pages=self.__settings.best_first_max_pages or math.inf,
        )
        config = self.__config(deep_crawl_strategy=strategy).clone(stream=True)
        # A streamed deep crawl is an async generator; a consumer that stops iterating
        # closes this generator, and `cancel()` then ends the underlying crawl.
        try:
            async for result in await self.__browser().arun(hub_url, config=config):
                if getattr(result, "success", False):
                    yield to_page(result)
        except Exception:
            logger.exception("best-first crawl failed: hub=%s", hub_url)
        finally:
            strategy.cancel()

    def __browser(self) -> AsyncWebCrawler:
        if self.__crawler is None:
            raise RuntimeError("Crawl4AiPageCrawler is used before start()")
        return self.__crawler

    def __config(
        self, *, article: bool = False, deep_crawl_strategy: Any = None
    ) -> CrawlerRunConfig:
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
            deep_crawl_strategy=deep_crawl_strategy,
            excluded_tags=ARTICLE_EXCLUDED_TAGS if article else EXCLUDED_TAGS,
            exclude_external_links=True,
            check_robots_txt=self.__settings.check_robots_txt,
            user_agent=self.__settings.user_agent,
            page_timeout=self.__settings.page_timeout_ms,
            wait_until="domcontentloaded",
            word_count_threshold=WORD_COUNT_THRESHOLD,
            semaphore_count=self.__settings.crawl_concurrency,
        )

    def __adaptive_config(self) -> AdaptiveConfig:
        settings = self.__settings
        llm_config = None
        if settings.adaptive_strategy in LLM_ADAPTIVE_STRATEGIES:
            llm_config = LLMConfig(
                provider=self.__llm.llm_provider(),
                api_token=self.__llm.llm_token(),
                base_url=self.__llm.llm_base_url(),
            )
        return AdaptiveConfig(
            confidence_threshold=settings.adaptive_confidence_threshold,
            max_depth=settings.adaptive_max_depth,
            max_pages=settings.adaptive_max_pages,
            top_k_links=settings.adaptive_top_k_links,
            min_gain_threshold=settings.adaptive_min_gain_threshold,
            strategy=settings.adaptive_strategy,
            query_llm_config=llm_config,
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
