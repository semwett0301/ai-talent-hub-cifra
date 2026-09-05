"""`ListingClassifier` — ask the crawl's LLM whether pages are listings, under one budget."""

import asyncio
from dataclasses import dataclass
from functools import partial

from common.core.llm import LlmCallBudget
from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import listing_llm_snapshot, pagination_link
from source_service.application.ports.scraping import CrawlLlm, FetchedPage, ListingVerdict
from source_service.domain.urls import normalize_url

logger = get_logger(__name__)


@dataclass(frozen=True)
class ClassifiedPage:
    """A page, what the model said about it, and the next listing page the verdict picked.
    The snapshot the model read never leaves the classifier."""

    page: FetchedPage
    verdict: ListingVerdict | None
    next_page: str | None


class ListingClassifier:
    """Holds no per-site state: one instance serves every crawl at once. The cap on how
    much one site may spend lives in the `LlmCallBudget` the caller opens with `budget()`
    and hands to every `classify` of that site."""

    def __init__(self, llm: CrawlLlm, settings: WebCrawlSettings) -> None:
        self.__llm = llm
        self.__settings = settings

    def budget(self) -> LlmCallBudget:
        """A fresh per-site budget; the caller passes it to every `classify` of one site."""
        return LlmCallBudget(
            max_calls=self.__settings.listing_max_pages_per_site,
            concurrency=self.__settings.listing_llm_concurrency,
        )

    async def classify(
        self, pages: list[FetchedPage], budget: LlmCallBudget
    ) -> list[ClassifiedPage]:
        """Classify every page concurrently; a page the budget can't afford is dropped
        before even building its snapshot."""
        results = await asyncio.gather(*(self.__classify_one(page, budget) for page in pages))
        classified = [entry for entry in results if entry is not None]

        logger.info(
            "listing pages classified: pages=%d classified=%d llm_calls=%d",
            len(pages),
            len(classified),
            budget.used,
        )
        return classified

    async def __classify_one(
        self, page: FetchedPage, budget: LlmCallBudget
    ) -> ClassifiedPage | None:
        url = normalize_url(page.url) or page.url
        return await budget.run(partial(self.__ask, url, page))

    async def __ask(self, url: str, page: FetchedPage) -> ClassifiedPage:
        snapshot = listing_llm_snapshot(page.html, base_url=url)
        verdict = await self.__llm.classify_listing(url, snapshot)

        next_page = pagination_link(snapshot, verdict.next_page_index) if verdict else None
        return ClassifiedPage(page, verdict, next_page)
