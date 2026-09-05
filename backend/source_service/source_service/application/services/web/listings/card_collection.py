"""`CardCollection` — read the hubs card by card into DISCOVERED articles."""

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import listing_cards, next_listing_page
from source_service.application.ports.scraping import FetchedPage, PageCrawler
from source_service.domain import Article, FreshnessWindow, Hub

logger = get_logger(__name__)


class CardCollection:
    """Cards in page order, hub after hub; the first card dated before the window ends its
    hub. Dedupe by URL, first sighting wins; capped by `max_article_candidates_per_site`."""

    def __init__(self, crawler: PageCrawler, settings: WebCrawlSettings) -> None:
        self.__crawler = crawler
        self.__settings = settings
        self.__window = FreshnessWindow(days=settings.days, timezone=settings.timezone)

    async def run(self, hubs: list[Hub]) -> list[Article]:
        found: dict[str, Article] = {}
        hub_ids = {hub.identity for hub in hubs}

        for hub in hubs:
            for card in await self.__traverse(hub, hub_ids):
                found.setdefault(card.url, card)

        cap = self.__settings.max_article_candidates_per_site
        cards = list(found.values())[: cap or None]
        logger.info("listing cards collected: hubs=%d cards=%d", len(hubs), len(cards))
        return cards

    async def __traverse(self, hub: Hub, hub_ids: set[str]) -> list[Article]:
        cards: list[Article] = []
        url: str | None = hub.url
        next_hint = hub.next_page
        seen: set[str] = set()
        cap = self.__settings.listing_max_pages_per_hub

        while url and url not in seen and (not cap or len(seen) < cap):
            seen.add(url)
            page = await self.__crawler.crawl_page(url)
            if page is None:
                break

            fresh, reached_old = self.__cards(page, hub, hub_ids)
            cards.extend(fresh)
            logger.info(
                "listing page read: hub=%s page=%d cards=%d reached_old=%s",
                hub.url,
                len(seen),
                len(fresh),
                reached_old,
            )
            if reached_old:
                break

            # The classifier's hint applies to the first hop only; then follow the markup.
            url = next_hint or next_listing_page(page.html, base_url=url)
            next_hint = None
        return cards

    def __cards(self, page: FetchedPage, hub: Hub, hub_ids: set[str]) -> tuple[list[Article], bool]:
        """Article-shaped cards until the first one dated before the window."""
        cards: list[Article] = []
        for card in listing_cards(
            page.html,
            base_url=page.url,
            timezone=self.__settings.timezone,
            score_threshold=self.__settings.candidate_score_threshold,
            hub_url=hub.url,
        ):
            if card.identity in hub_ids:
                continue
            if card.card_published_at and self.__window.is_before(card.card_published_at):
                return cards, True
            cards.append(card)
        return cards, False
