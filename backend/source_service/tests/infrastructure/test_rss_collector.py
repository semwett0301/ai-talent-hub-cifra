import uuid

import pytest
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas import RssLink, Source
from source_service.application.ports.scraping import FeedEntry
from source_service.application.services.dedup import StoredNewsFilter
from source_service.infrastructure.collectors.rss import RssCollector

MAIN_FEED = "https://example.test/rss"
SECTION_FEED = "https://example.test/news/rss"
SHARED_ENTRY = "https://example.test/news/shared"
SECTION_ENTRY = "https://example.test/news/section-only"


def entry(url: str, title: str = "Title") -> FeedEntry:
    return FeedEntry(url=url, title=title, summary="Summary", published_at=None, tags=["Tech"])


class FakeFeedReader:
    def __init__(self, feeds: dict[str, list[FeedEntry]]) -> None:
        self.feeds = feeds
        self.read_urls: list[str] = []

    async def read(self, feed_url: str) -> list[FeedEntry]:
        self.read_urls.append(feed_url)
        return self.feeds.get(feed_url, [])


class UnreachablePageFetcher:
    def __init__(self) -> None:
        self.fetched_urls: list[str] = []

    async def fetch(self, url: str) -> str | None:
        self.fetched_urls.append(url)
        return None


class FakeStoredNewsIndex:
    def __init__(self, *stored: str) -> None:
        self.stored = set(stored)

    async def list_stored_urls(self, urls: list[str]) -> set[str]:
        return self.stored.intersection(urls)


def rss_collector(reader: FakeFeedReader, *stored: str) -> RssCollector:
    return RssCollector(
        reader, UnreachablePageFetcher(), StoredNewsFilter(FakeStoredNewsIndex(*stored), "rss")
    )


def rss_source(*feed_urls: str) -> Source:
    source = Source(
        id=uuid.uuid4(),
        name="Example",
        link="https://example.test",
        type=SourceType.RSS,
        reliability=SourceReliability.MEDIUM,
    )
    source.rss_links = [RssLink(url=url) for url in feed_urls]
    return source


@pytest.mark.asyncio
async def test_reads_every_feed_and_collects_a_shared_entry_once():
    reader = FakeFeedReader(
        {
            MAIN_FEED: [entry(SHARED_ENTRY)],
            SECTION_FEED: [entry(SHARED_ENTRY), entry(SECTION_ENTRY)],
        }
    )
    collector = rss_collector(reader)

    news = await collector.fetch(rss_source(MAIN_FEED, SECTION_FEED))

    assert reader.read_urls == [MAIN_FEED, SECTION_FEED]
    assert sorted(item.url for item in news) == sorted([SHARED_ENTRY, SECTION_ENTRY])


@pytest.mark.asyncio
async def test_takes_the_entry_as_the_first_feed_listed_it():
    reader = FakeFeedReader(
        {MAIN_FEED: [entry(SHARED_ENTRY, "First")], SECTION_FEED: [entry(SHARED_ENTRY, "Second")]}
    )
    collector = rss_collector(reader)

    news = await collector.fetch(rss_source(MAIN_FEED, SECTION_FEED))

    assert [item.title for item in news] == ["First"]


@pytest.mark.asyncio
async def test_maps_the_feed_entry_onto_the_flat_news_fields():
    source = rss_source(MAIN_FEED)
    reader = FakeFeedReader({MAIN_FEED: [entry(SECTION_ENTRY)]})
    collector = rss_collector(reader)

    [item] = await collector.fetch(source)

    assert item.source_id == source.id
    assert item.source_name == "Example"
    assert item.text == "Summary"  # the page was unreachable: the feed summary stands in
    assert item.excerpt == "Summary"
    assert item.source_tags == ["Tech"]


@pytest.mark.asyncio
async def test_a_source_without_feeds_yields_nothing():
    reader = FakeFeedReader({})
    collector = rss_collector(reader)

    assert await collector.fetch(rss_source()) == []
    assert reader.read_urls == []


@pytest.mark.asyncio
async def test_a_stored_entry_is_neither_fetched_nor_collected_again():
    reader = FakeFeedReader({MAIN_FEED: [entry(SHARED_ENTRY), entry(SECTION_ENTRY)]})
    page_fetcher = UnreachablePageFetcher()
    stored_news = StoredNewsFilter(FakeStoredNewsIndex(SHARED_ENTRY), "rss")
    collector = RssCollector(reader, page_fetcher, stored_news)

    news = await collector.fetch(rss_source(MAIN_FEED))

    assert [item.url for item in news] == [SECTION_ENTRY]
    assert page_fetcher.fetched_urls == [SECTION_ENTRY]


@pytest.mark.asyncio
async def test_a_feed_with_nothing_new_touches_no_page():
    reader = FakeFeedReader({MAIN_FEED: [entry(SHARED_ENTRY)]})
    page_fetcher = UnreachablePageFetcher()
    stored_news = StoredNewsFilter(FakeStoredNewsIndex(SHARED_ENTRY), "rss")
    collector = RssCollector(reader, page_fetcher, stored_news)

    assert await collector.fetch(rss_source(MAIN_FEED)) == []
    assert page_fetcher.fetched_urls == []
