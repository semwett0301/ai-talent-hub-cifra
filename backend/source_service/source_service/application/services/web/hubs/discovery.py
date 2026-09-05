"""`HubDiscovery` — find the pages of a site that list its publications."""

from collections.abc import Iterator

from common.core.llm import LlmCallBudget
from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.ports.scraping import FetchedPage, ListingVerdict, PageCrawler
from source_service.domain import Article, Hub, HubOrigin, Site, is_article_like, rank_hubs
from source_service.domain.urls import is_pagination_url, normalize_url

from .listing_classifier import ClassifiedPage, ListingClassifier
from .state import Frontier

logger = get_logger(__name__)


def _may_lead_to_listings(verdict: ListingVerdict | None) -> bool:
    """Expand one level deeper when the classifier failed on the page or said the
    listings are one hop below."""
    if verdict is None:
        return True
    return not verdict.is_listing and verdict.may_contain_news_listings


def _page_links(page: FetchedPage, site: Site, max_article_score: float) -> Iterator[str]:
    """Same-site links on one page that are neither pagination nor article-shaped."""
    base = normalize_url(page.url)
    if not base:
        return

    for link in page.links:
        href = normalize_url(link.href, base=base)
        if not href or not site.owns(href) or is_pagination_url(href):
            continue

        probe = Article(url=href, title_hint=link.text.strip() or None)
        if not is_article_like(probe, max_article_score):
            yield href


def _child_links(pages: list[FetchedPage], site: Site, max_article_score: float) -> list[str]:
    """Same-site links across all pages, neither pagination nor article-shaped."""
    return [href for page in pages for href in _page_links(page, site, max_article_score)]


class HubDiscovery:
    """Home page → its links → (their links) → "is this a listing?" via the classifier,
    never more than `listing_discovery_max_depth` clicks deep. Without a classifier the
    home page is the only hub."""

    def __init__(
        self,
        crawler: PageCrawler,
        classifier: ListingClassifier | None,
        settings: WebCrawlSettings,
    ) -> None:
        self.__crawler = crawler
        self.__classifier = classifier
        self.__settings = settings

    async def run(self, site: Site) -> list[Hub]:
        if self.__classifier is None:
            logger.info(
                "hub discovery skipped: site=%s (no classifier, home page is the hub)", site.seed
            )
            return [Hub.build(site.seed, HubOrigin.SEED, site.name)]

        # Fresh per site: never stored on `self` — one `HubDiscovery` instance serves
        # every site the scheduler crawls, often several at once.
        frontier = Frontier(self.__settings.listing_max_pages_per_site)
        budget = self.__classifier.budget()

        found = await self.__discover(site, frontier, budget)
        if not found:
            # A homepage can itself be the only listing (common for small sites).
            logger.info("listing search empty: site=%s (falling back to the home page)", site.seed)
            found = [Hub.build(site.seed, HubOrigin.SEED, site.name)]

        hubs = rank_hubs(found)[: self.__settings.max_hubs_per_site or None]
        logger.info(
            "hubs discovered: site=%s hubs=%d pages=%d llm_calls=%d",
            site.seed,
            len(hubs),
            frontier.pages_seen,
            budget.used,
        )
        return hubs

    async def __discover(self, site: Site, frontier: Frontier, budget: LlmCallBudget) -> list[Hub]:
        home = await self.__scrape(frontier, [site.seed], 0)
        if self.__settings.listing_discovery_max_depth == 0:
            return self.__accept(await self.__classify(home, budget), 0)

        found: list[Hub] = []
        pages, depth = home, 1

        while True:
            links = _child_links(pages, site, self.__settings.hub_link_max_article_score)
            accepted, expand = await self.__discover_depth(frontier, budget, links, depth)
            found += accepted

            if depth >= self.__settings.listing_discovery_max_depth or not expand:
                break

            pages, depth = expand, depth + 1

        return found

    async def __discover_depth(
        self, frontier: Frontier, budget: LlmCallBudget, links: list[str], depth: int
    ) -> tuple[list[Hub], list[FetchedPage]]:
        """One hop: crawl the given links, classify, accept the listings, and say which
        pages are worth expanding one hop further."""
        pages = await self.__scrape(frontier, links, depth)
        classified = await self.__classify(pages, budget)
        accepted = self.__accept(classified, depth)

        expand = [entry.page for entry in classified if _may_lead_to_listings(entry.verdict)]
        logger.info(
            "listing frontier branched: depth=%d listings=%d expand=%d pruned=%d",
            depth,
            len(accepted),
            len(expand),
            len(pages) - len(accepted) - len(expand),
        )
        return accepted, expand

    async def __classify(
        self, pages: list[FetchedPage], budget: LlmCallBudget
    ) -> list[ClassifiedPage]:
        assert self.__classifier is not None
        return await self.__classifier.classify(pages, budget)

    async def __scrape(self, frontier: Frontier, urls: list[str], depth: int) -> list[FetchedPage]:
        batch = frontier.take(urls)
        if not batch:
            return []

        pages = await self.__crawler.crawl_pages(batch)
        logger.info(
            "listing frontier crawled: depth=%d requested=%d ok=%d", depth, len(batch), len(pages)
        )
        return pages

    def __accept(self, classified: list[ClassifiedPage], depth: int) -> list[Hub]:
        hubs = (self.__to_hub(entry, depth) for entry in classified)
        return [hub for hub in hubs if hub is not None]

    def __to_hub(self, entry: ClassifiedPage, depth: int) -> Hub | None:
        """The page as a hub, or `None` when the model did not call it a listing
        confidently enough."""
        verdict = entry.verdict
        if not verdict or not verdict.is_listing:
            return None
        if verdict.confidence < self.__settings.listing_llm_min_confidence:
            return None

        url = normalize_url(entry.page.url) or entry.page.url
        logger.info(
            "listing accepted: depth=%d confidence=%.2f url=%s reason=%s",
            depth,
            verdict.confidence,
            url,
            verdict.rationale,
        )
        return Hub.build(
            url, HubOrigin.LISTING, entry.page.title, entry.page.markdown, next_page=entry.next_page
        )
