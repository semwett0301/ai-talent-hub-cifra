"""`HubDiscovery` — find the pages of a site that list its publications."""

import asyncio
from dataclasses import dataclass, field

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import listing_llm_snapshot, pagination_link
from source_service.application.ports.scraping import (
    CrawlLlm,
    FetchedPage,
    ListingVerdict,
    PageCrawler,
)
from source_service.domain import Article, Hub, HubOrigin, Site, is_article_like, rank_hubs
from source_service.domain.urls import is_pagination_url, listing_identity, normalize_url

logger = get_logger(__name__)

# Links that already look like one article are not candidates for being a listing.
HUB_LINK_MAX_ARTICLE_SCORE = 0.35
SEED_DEPTH = 0


def _may_lead_to_listings(verdict: ListingVerdict | None) -> bool:
    """Expand one level deeper when the classifier failed on the page or said the
    listings are one hop below."""
    if verdict is None:
        return True
    return not verdict.is_listing and verdict.may_contain_news_listings


@dataclass
class _Frontier:
    """Per-site discovery state: what was already fetched and how much LLM was spent."""

    seen: set[str] = field(default_factory=set)
    llm_calls: int = 0


@dataclass(frozen=True)
class _Classified:
    page: FetchedPage
    depth: int
    snapshot: dict[str, object]
    verdict: ListingVerdict | None


class HubDiscovery:
    """Home page → its links → (their links) → "is this a listing?" via the classifier,
    never more than `listing_discovery_max_depth` clicks deep. Without a classifier the
    home page is the only hub."""

    def __init__(
        self,
        crawler: PageCrawler,
        classifier: CrawlLlm | None,
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

        frontier = _Frontier()
        found = await self.__discover(site, frontier)
        if not found:
            # A homepage can itself be the only listing (common for small sites).
            seed_hub = Hub.build(site.seed, HubOrigin.SEED, site.name)
            found[seed_hub.identity] = seed_hub

        cap = self.__settings.max_hubs_per_site
        hubs = rank_hubs(found.values())[: cap or None]
        logger.info(
            "hubs discovered: site=%s hubs=%d pages=%d llm_calls=%d",
            site.seed,
            len(hubs),
            len(frontier.seen),
            frontier.llm_calls,
        )
        return hubs

    async def __discover(self, site: Site, frontier: _Frontier) -> dict[str, Hub]:
        home = await self.__scrape(frontier, [site.seed], SEED_DEPTH)
        if self.__settings.listing_discovery_max_depth == SEED_DEPTH:
            return self.__accept(await self.__classify(frontier, home, SEED_DEPTH))

        found: dict[str, Hub] = {}
        pages_at_depth, depth = home, 1
        while True:
            pages = await self.__scrape(frontier, self.__child_links(pages_at_depth, site), depth)
            classified = await self.__classify(frontier, pages, depth)
            accepted = self.__accept(classified)
            found.update(accepted)

            expand = [entry.page for entry in classified if _may_lead_to_listings(entry.verdict)]
            logger.info(
                "listing frontier branched: depth=%d listings=%d expand=%d pruned=%d",
                depth,
                len(accepted),
                len(expand),
                len(pages) - len(accepted) - len(expand),
            )
            if depth >= self.__settings.listing_discovery_max_depth or not expand:
                break
            pages_at_depth, depth = expand, depth + 1
        return found

    def __child_links(self, pages: list[FetchedPage], site: Site) -> list[str]:
        """Same-site links that are neither pagination nor article-shaped."""
        links: list[str] = []
        for page in pages:
            base = normalize_url(page.url)
            if not base:
                continue
            for link in page.links:
                href = normalize_url(link.href, base=base)
                if not href or not site.owns(href) or is_pagination_url(href):
                    continue
                probe = Article(url=href, title_hint=link.text.strip() or None)
                if not is_article_like(probe, HUB_LINK_MAX_ARTICLE_SCORE):
                    links.append(href)
        return links

    async def __scrape(self, frontier: _Frontier, urls: list[str], depth: int) -> list[FetchedPage]:
        max_pages = self.__settings.listing_discovery_max_pages
        batch: list[str] = []
        for url in urls:
            identity = listing_identity(url)
            if identity in frontier.seen:
                continue
            if max_pages and len(frontier.seen) + len(batch) >= max_pages:
                break
            frontier.seen.add(identity)
            batch.append(url)

        if not batch:
            return []
        pages = await self.__crawler.crawl_pages(batch)
        logger.info(
            "listing frontier crawled: depth=%d requested=%d ok=%d", depth, len(batch), len(pages)
        )
        return pages

    async def __classify(
        self, frontier: _Frontier, pages: list[FetchedPage], depth: int
    ) -> list[_Classified]:
        assert self.__classifier is not None
        classifier = self.__classifier
        limit = self.__settings.listing_llm_max_calls_per_site
        probes = pages[: max(0, limit - frontier.llm_calls)] if limit else pages
        frontier.llm_calls += len(probes)
        gate = asyncio.Semaphore(self.__settings.listing_llm_concurrency)

        async def classify(page: FetchedPage) -> _Classified:
            url = normalize_url(page.url) or page.url
            snapshot = listing_llm_snapshot(page.html, base_url=url)
            async with gate:
                verdict = await classifier.classify_listing(url, snapshot)
            return _Classified(page, depth, snapshot, verdict)

        logger.info("listing pages classified: depth=%d requests=%d", depth, len(probes))
        return list(await asyncio.gather(*(classify(page) for page in probes)))

    def __accept(self, classified: list[_Classified]) -> dict[str, Hub]:
        found: dict[str, Hub] = {}
        for entry in classified:
            verdict = entry.verdict
            if (
                not verdict
                or not verdict.is_listing
                or verdict.confidence < self.__settings.listing_llm_min_confidence
            ):
                continue

            url = normalize_url(entry.page.url) or entry.page.url
            hub = Hub.build(
                url,
                HubOrigin.LISTING,
                entry.page.title,
                entry.page.markdown,
                next_page=pagination_link(entry.snapshot, verdict.next_page_index),
            )
            found[hub.identity] = hub
            logger.info(
                "listing accepted: depth=%d confidence=%.2f url=%s reason=%s",
                entry.depth,
                verdict.confidence,
                url,
                verdict.rationale,
            )
        return found
