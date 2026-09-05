import pytest
from common.core.settings import WebCrawlSettings
from source_service.application.ports.scraping import FetchedPage, ListingVerdict, PageLink
from source_service.application.services.web.hubs import HubDiscovery, ListingClassifier
from source_service.domain import HubOrigin, Site

SITE = Site(url="https://example.test", name="Example")


def page(url: str, links: tuple[PageLink, ...] = (), html: str = "<html></html>") -> FetchedPage:
    return FetchedPage(url=url, final_url=url, html=html, markdown="", title=None, links=links)


class FakeCrawler:
    def __init__(self, pages: dict[str, FetchedPage]):
        self.pages = pages
        self.requested: list[str] = []

    async def crawl_page(self, url):
        return self.pages.get(url)

    async def crawl_pages(self, urls):
        self.requested += urls
        return [self.pages[u] for u in urls if u in self.pages]

    async def crawl_articles(self, urls):
        return await self.crawl_pages(urls)


class FakeLlm:
    def __init__(self, listings: set[str], expandable: frozenset[str] = frozenset()):
        self.listings = listings
        self.expandable = expandable

    async def resolve_publication_date(self, url, text):
        return None

    async def classify_listing(self, url, snapshot):
        return ListingVerdict(
            is_listing=url in self.listings,
            may_contain_news_listings=url in self.expandable,
            confidence=0.9,
            rationale="test",
            next_page_index=0 if url in self.listings else None,
        )


@pytest.mark.asyncio
async def test_without_classifier_home_page_is_the_only_hub_and_nothing_is_fetched():
    crawler = FakeCrawler({})
    hubs = await HubDiscovery(crawler, None, WebCrawlSettings()).run(SITE)

    assert [(h.url, h.origin) for h in hubs] == [("https://example.test/", HubOrigin.SEED)]
    assert crawler.requested == []


@pytest.mark.asyncio
async def test_classifier_confirmed_listing_becomes_a_hub_with_its_next_page():
    news_html = "<main><a href='/news?page=2' rel='next'>Дальше</a></main>"
    crawler = FakeCrawler(
        {
            "https://example.test/": page(
                "https://example.test/",
                links=(PageLink("/news", "Новости компании"), PageLink("/about", "О компании")),
            ),
            "https://example.test/news": page("https://example.test/news", html=news_html),
            "https://example.test/about": page("https://example.test/about"),
        }
    )
    settings = WebCrawlSettings()
    classifier = ListingClassifier(FakeLlm({"https://example.test/news"}), settings)
    discovery = HubDiscovery(crawler, classifier, settings)

    hubs = await discovery.run(SITE)

    assert [h.url for h in hubs] == ["https://example.test/news"]
    assert hubs[0].origin is HubOrigin.LISTING
    assert hubs[0].next_page == "https://example.test/news?page=2"


@pytest.mark.asyncio
async def test_default_depth_reaches_a_listing_three_clicks_deep():
    """`listing_discovery_max_depth` defaults to 3 — the loop must actually get there."""
    section = "https://example.test/section"
    subsection = "https://example.test/section/sub"
    listing = "https://example.test/section/sub/news"
    crawler = FakeCrawler(
        {
            "https://example.test/": page(
                "https://example.test/", links=(PageLink("/section", "Раздел компании"),)
            ),
            section: page(section, links=(PageLink("/section/sub", "Подраздел новостей"),)),
            subsection: page(subsection, links=(PageLink("/section/sub/news", "Все новости"),)),
            listing: page(listing),
        }
    )
    settings = WebCrawlSettings()
    llm = FakeLlm(listings={listing}, expandable=frozenset({section, subsection}))
    discovery = HubDiscovery(crawler, ListingClassifier(llm, settings), settings)

    hubs = await discovery.run(SITE)

    assert [h.url for h in hubs] == [listing]
