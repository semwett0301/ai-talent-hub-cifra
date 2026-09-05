"""`FallbackDiscovery` — adaptive + best-first exploration for sites without usable listings."""

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import extract_publication_date_signal, parse_date
from source_service.application.ports.scraping import FetchedPage, PageCrawler
from source_service.domain import (
    Article,
    ArticleOrigin,
    FreshnessWindow,
    Hub,
    HubOrigin,
    Site,
    merge_hubs,
    select_candidates,
    select_hubs,
)
from source_service.domain.urls import normalize_url

logger = get_logger(__name__)


class FallbackDiscovery:
    """Runs only when the listings yielded nothing: explore from the home page, keep the
    hub-like pages, deep-crawl below each, keep the article-shaped URLs."""

    def __init__(self, crawler: PageCrawler, settings: WebCrawlSettings) -> None:
        self.__crawler = crawler
        self.__settings = settings

    async def run(self, site: Site) -> list[Article]:
        adaptive = await self.__adaptive(site.seed)
        hubs = self.__hubs_from(site, adaptive, HubOrigin.ADAPTIVE)
        if not hubs:
            hubs = [Hub.build(site.seed, HubOrigin.SEED, site.label)]

        best: dict[str, list[FetchedPage]] = {}
        for hub in self.__limit(hubs):
            best[hub.url] = await self.__best_first(hub.url)
        below_hubs = [page for pages in best.values() for page in pages]
        hubs = self.__limit(
            merge_hubs(hubs + self.__hubs_from(site, below_hubs, HubOrigin.BEST_FIRST))
        )

        candidates = self.__candidates_from(site, adaptive, best, hubs)
        logger.info(
            "fallback discovery finished: site=%s hubs=%d candidates=%d",
            site.seed,
            len(hubs),
            len(candidates),
        )
        return candidates

    async def __adaptive(self, seed: str) -> list[FetchedPage]:
        if not self.__settings.adaptive_enabled:
            return []
        pages = await self.__crawler.adaptive_discover(seed)
        logger.info("adaptive crawl finished: seed=%s pages=%d", seed, len(pages))
        return pages

    async def __best_first(self, hub_url: str) -> list[FetchedPage]:
        """Take pages as the crawler yields them; leave the loop once a due page's
        publication date is before the freshness window — that ends the crawl."""
        if not self.__settings.best_first_fallback:
            return []
        window = FreshnessWindow(days=self.__settings.days, timezone=self.__settings.timezone)
        pages: list[FetchedPage] = []
        pages_seen = 0

        async for page in self.__crawler.best_first_discover(hub_url):
            pages.append(page)
            pages_seen += 1
            if self.__is_date_probe_due(pages_seen) and self.__is_out_of_scope(
                page, pages_seen, window
            ):
                logger.info("best-first crawl stopped: hub=%s page=%d", hub_url, pages_seen)
                break

        logger.info("best-first crawl finished: hub=%s pages=%d", hub_url, len(pages))
        return pages

    def __is_date_probe_due(self, pages_seen: int) -> bool:
        """Probe from `date_probe_start_page` on, every `date_probe_interval_pages` pages."""
        start = self.__settings.date_probe_start_page
        interval = self.__settings.date_probe_interval_pages
        return pages_seen >= start and (pages_seen - start) % interval == 0

    def __is_out_of_scope(
        self, page: FetchedPage, pages_seen: int, window: FreshnessWindow
    ) -> bool:
        signal = extract_publication_date_signal(page.html)
        value = parse_date(signal.value, self.__settings.timezone) if signal.value else None
        if value is None:
            logger.info("date probe inconclusive: page=%d url=%s", pages_seen, page.url)
            return False

        is_old = window.is_before(value)
        logger.info(
            "date probed: page=%d date=%s source=%s old=%s",
            pages_seen,
            value.isoformat(),
            signal.source,
            is_old,
        )
        return is_old and self.__settings.stop_hub_on_out_of_scope_probe

    def __limit(self, hubs: list[Hub]) -> list[Hub]:
        cap = self.__settings.max_hubs_per_site
        return hubs[:cap] if cap else hubs

    def __hubs_from(self, site: Site, pages: list[FetchedPage], origin: HubOrigin) -> list[Hub]:
        """Every visited page and every same-site link on it is a hub sighting; the domain
        keeps the ones that look like listings."""
        sightings: list[Hub] = []
        for page in pages:
            url = normalize_url(page.url)
            if not url or not site.owns(url):
                continue
            sightings.append(Hub.build(url, origin, page.title, page.markdown))
            for link in page.links:
                href = normalize_url(link.href, base=url)
                if href and site.owns(href):
                    sightings.append(Hub.build(href, origin, link.text.strip()))
        return select_hubs(sightings, self.__settings.min_hub_score)

    def __candidates_from(
        self,
        site: Site,
        adaptive: list[FetchedPage],
        best: dict[str, list[FetchedPage]],
        hubs: list[Hub],
    ) -> list[Article]:
        """Every visited page and every link on it is an article sighting, except the hubs
        themselves and anything off-site; the domain keeps the article-shaped ones."""
        sightings = self.__sightings(adaptive, None, ArticleOrigin.ADAPTIVE, site)
        for hub_url, pages in best.items():
            sightings += self.__sightings(pages, hub_url, ArticleOrigin.BEST_FIRST, site)

        hub_urls = {hub.url for hub in hubs}
        on_site = [a for a in sightings if a.url not in hub_urls and site.owns(a.url)]
        candidates = select_candidates(on_site, self.__settings.candidate_score_threshold)
        cap = self.__settings.max_article_candidates_per_site
        return candidates[:cap] if cap else candidates

    @staticmethod
    def __sightings(
        pages: list[FetchedPage], hub_url: str | None, origin: ArticleOrigin, site: Site
    ) -> list[Article]:
        sightings: list[Article] = []
        for page in pages:
            page_url = normalize_url(page.url)
            if page_url:
                sightings.append(
                    Article(
                        url=page_url,
                        hub_url=hub_url,
                        title_hint=page.title,
                        origin=origin,
                        metadata=page.metadata,
                    )
                )
            for link in page.links:
                href = normalize_url(link.href, base=hub_url or page_url or site.seed)
                if href:
                    sightings.append(
                        Article(
                            url=href,
                            hub_url=hub_url or page_url,
                            title_hint=link.text.strip() or None,
                            origin=ArticleOrigin.LINK,
                        )
                    )
        return sightings
