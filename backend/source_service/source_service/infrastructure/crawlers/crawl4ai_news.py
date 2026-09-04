from __future__ import annotations

import logging
import math
from collections.abc import AsyncIterable
from typing import Any

from crawl4ai import (
    AdaptiveConfig,
    AdaptiveCrawler,
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from source_service.application.web_crawl.config import EnvSettings
from source_service.application.web_crawl.date_utils import is_older_than_window, parse_date
from source_service.application.web_crawl.html_meta import extract_publication_date_signal
from source_service.application.web_crawl.settings import RuntimeSettings

from .crawl4ai_llm import Crawl4AILlmMixin
from .crawl4ai_support import is_date_probe_page, materialize_results, selector_score

logger = logging.getLogger(__name__)

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


class Crawl4AIClient(Crawl4AILlmMixin):
    def __init__(self, settings: RuntimeSettings, env: EnvSettings):
        self.settings = settings
        self.env = env
        self.crawler: AsyncWebCrawler | None = None
        self.article_css_selector: str | None = None
        self.article_text_strategy: dict[str, object] = {
            "selector": None,
            "reason": "not_calibrated",
        }

    async def __aenter__(self):
        self.crawler = AsyncWebCrawler(
            config=BrowserConfig(headless=True, text_mode=True, verbose=False)
        )
        await self.crawler.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.crawler:
            await self.crawler.close()

    def _require_crawler(self) -> AsyncWebCrawler:
        if self.crawler is None:
            raise RuntimeError("Crawl4AIClient must be used as an async context manager")
        return self.crawler

    def _common_config(
        self,
        *,
        markdown_generator=None,
        deep_crawl_strategy=None,
        article_mode: bool = False,
        extraction_strategy=None,
    ):
        excluded = ["script", "style", "noscript", "svg", "form"]
        if article_mode:
            excluded += ["nav", "footer", "aside"]
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            deep_crawl_strategy=deep_crawl_strategy,
            extraction_strategy=extraction_strategy,
            excluded_tags=excluded,
            exclude_external_links=True,
            check_robots_txt=self.settings.check_robots_txt,
            user_agent=self.settings.user_agent,
            page_timeout=self.settings.page_timeout_ms,
            wait_until="domcontentloaded",
            word_count_threshold=10,
            semaphore_count=self.settings.crawl_concurrency,
        )

    async def adaptive_discover(self, seed_url: str):
        assert self.crawler is not None
        adaptive_llm = (
            self._llm_config() if self.settings.adaptive_strategy in {"embedding", "llm"} else None
        )
        config = AdaptiveConfig(
            confidence_threshold=self.settings.adaptive_confidence_threshold,
            max_depth=self.settings.adaptive_max_depth,
            max_pages=self.settings.adaptive_max_pages,
            top_k_links=self.settings.adaptive_top_k_links,
            min_gain_threshold=self.settings.adaptive_min_gain_threshold,
            strategy=self.settings.adaptive_strategy,
            query_llm_config=adaptive_llm,
        )
        adaptive = AdaptiveCrawler(self.crawler, config=config)
        state = await adaptive.digest(start_url=seed_url, query=self.settings.discovery_query)
        return state, float(getattr(adaptive, "confidence", 0.0) or 0.0)

    async def best_first_discover(self, seed_or_hub_url: str) -> tuple[list, dict]:
        assert self.crawler is not None
        strategy = BestFirstCrawlingStrategy(
            max_depth=self.settings.best_first_depth,
            include_external=False,
            url_scorer=KeywordRelevanceScorer(keywords=NEWS_KEYWORDS, weight=0.7),
            max_pages=math.inf
            if self.settings.best_first_max_pages == 0
            else self.settings.best_first_max_pages,
        )
        value = await self.crawler.arun(
            seed_or_hub_url,
            config=self._common_config(deep_crawl_strategy=strategy).clone(stream=True),
        )
        results: list = []
        stats: dict[str, Any] = {
            "pages_crawled": 0,
            "date_probes": 0,
            "date_probe_history": [],
            "stopped_on_out_of_scope_probe": False,
            "stop_probe_url": None,
            "stop_probe_date": None,
            "stop_probe_source": None,
        }

        async def inspect(result) -> None:
            if not getattr(result, "success", False):
                return
            stats["pages_crawled"] = int(stats["pages_crawled"] or 0) + 1
            page_number = int(stats["pages_crawled"])
            starts = self.settings.date_probe_start_page
            interval = self.settings.date_probe_interval_pages
            should_probe = is_date_probe_page(page_number, starts, interval)
            if not should_probe:
                return
            stats["date_probes"] = int(stats["date_probes"] or 0) + 1
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None) or ""
            signal = extract_publication_date_signal(html)
            published_at = (
                parse_date(signal.value, self.settings.timezone) if signal.value else None
            )
            is_old = published_at is not None and is_older_than_window(
                published_at, self.settings.days, self.settings.timezone
            )
            probe = {
                "page_number": page_number,
                "url": str(getattr(result, "url", "")),
                "published_at": published_at.isoformat() if published_at else None,
                "date_source": signal.source,
                "out_of_scope": is_old,
            }
            history = stats["date_probe_history"]
            if isinstance(history, list) and len(history) < 100:
                history.append(probe)
            if published_at is None:
                logger.info(
                    "Date probe page %d: no reliable publication date (%s)",
                    page_number,
                    probe["url"],
                )
                return
            logger.info(
                "Date probe page %d: %s via %s; out_of_scope=%s",
                page_number,
                published_at.isoformat(),
                signal.source,
                is_old,
            )
            if not is_old:
                return
            if self.settings.stop_hub_on_out_of_scope_probe:
                stats["stopped_on_out_of_scope_probe"] = True
                stats["stop_probe_url"] = str(getattr(result, "url", ""))
                stats["stop_probe_date"] = published_at.isoformat()
                stats["stop_probe_source"] = signal.source
                logger.info(
                    "Stopping hub crawl after out-of-scope date probe on page %d", page_number
                )
                strategy.cancel()

        if isinstance(value, AsyncIterable) or hasattr(value, "__aiter__"):
            async for result in value:
                if getattr(result, "success", False):
                    results.append(result)
                await inspect(result)
        else:
            for result in await materialize_results(value):
                if getattr(result, "success", False):
                    results.append(result)
                await inspect(result)
        return results, stats

    async def crawl_page(self, url: str):
        """Fetch one shallow discovery/listing page without deep crawling."""
        assert self.crawler is not None
        value = await self.crawler.arun(url, config=self._common_config())
        results = await materialize_results(value)
        return next((result for result in results if getattr(result, "success", False)), None)

    async def crawl_pages(self, urls: list[str]) -> list:
        """Fetch one discovery frontier concurrently; no LLM work is mixed in."""
        assert self.crawler is not None
        if not urls:
            return []
        config = self._common_config()
        try:
            value = await self.crawler.arun_many(urls, config=config)
            return [
                result
                for result in await materialize_results(value)
                if getattr(result, "success", False)
            ]
        except Exception:
            logger.exception(
                "Listing frontier batch failed; retrying %d pages individually", len(urls)
            )
            out = []
            for url in urls:
                result = await self.crawl_page(url)
                if result is not None:
                    out.append(result)
            return out

    async def calibrate_article_text(self, sample_url: str) -> dict[str, object]:
        """Choose a generic article container from one real article for this site."""
        sample = await self.crawl_page(sample_url)
        html = getattr(sample, "html", None) or getattr(sample, "cleaned_html", None) or ""
        choices = ["article", "main", "[role='main']", None]
        ranked = [(selector_score(html, selector), selector) for selector in choices]
        (score, words), selector = max(ranked, key=lambda item: item[0][0])
        # Do not apply an accidental tiny element; the document-level filter is
        # safer in that case.
        self.article_css_selector = selector if words >= self.settings.min_article_words else None
        self.article_text_strategy = {
            "selector": self.article_css_selector,
            "sample_url": sample_url,
            "sample_words": words,
            "score": round(score, 2),
            "reason": "highest_prose_density_of_article_main_or_document",
        }
        logger.info(
            "[text/calibration] selector=%s sample_words=%d score=%.0f url=%s",
            self.article_css_selector or "document",
            words,
            score,
            sample_url,
        )
        return dict(self.article_text_strategy)

    async def crawl_articles(self, urls: list[str]) -> list:
        assert self.crawler is not None
        generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=self.settings.pruning_threshold,
                threshold_type="fixed",
                min_word_threshold=self.settings.pruning_min_words,
            )
        )
        config = self._common_config(markdown_generator=generator, article_mode=True)
        # Keep page HTML intact: publication-date extraction needs the complete
        # DOM. The calibrated selector is applied locally by ArticleExtractor
        # to its text field, after date metadata has been read.
        config.only_text = False
        out: list = []
        batch_size = max(1, self.settings.article_batch_size)
        for i in range(0, len(urls), batch_size):
            chunk = urls[i : i + batch_size]
            try:
                values = await self.crawler.arun_many(chunk, config=config)
                out.extend(await materialize_results(values))
            except Exception:
                logger.exception("Batch crawl failed; retrying %d URLs individually", len(chunk))
                for url in chunk:
                    try:
                        value = await self.crawler.arun(url, config=config)
                        out.extend(await materialize_results(value))
                    except Exception:
                        logger.exception("Article crawl failed: %s", url)
        return [r for r in out if getattr(r, "success", False)]
