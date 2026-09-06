import pytest
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas import RssLink, Source
from source_service.application.ports.scraping import FeedEntry
from source_service.infrastructure.collectors.rss import RssCollector

MAIN_FEED = "https://example.test/rss"
SECTION_FEED = "https://example.test/news/rss"
SHARED_ENTRY = "https://example.test/news/shared"
SECTION_ENTRY = "https://example.test/news/section-only"


def entry(url: str) -> FeedEntry:
    return FeedEntry(url=url, title="Title", summary="Summary", published_at=None)


class FakeFeedReader:
    def __init__(self, feeds: dict[str, list[FeedEntry]]) -> None:
        self.feeds = feeds
        self.read_urls: list[str] = []

    async def read(self, feed_url: str) -> list[FeedEntry]:
        self.read_urls.append(feed_url)
        return self.feeds.get(feed_url, [])


class UnreachablePageFetcher:
    async def fetch(self, url: str) -> str | None:
        return None


def rss_source(*feed_urls: str) -> Source:
    source = Source(
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
    collector = RssCollector(reader, UnreachablePageFetcher())

    news = await collector.fetch(rss_source(MAIN_FEED, SECTION_FEED))

    assert reader.read_urls == [MAIN_FEED, SECTION_FEED]
    assert sorted(item.url for item in news) == sorted([SHARED_ENTRY, SECTION_ENTRY])


@pytest.mark.asyncio
async def test_remembers_which_feed_listed_the_entry_first():
    reader = FakeFeedReader({MAIN_FEED: [entry(SHARED_ENTRY)], SECTION_FEED: [entry(SHARED_ENTRY)]})
    collector = RssCollector(reader, UnreachablePageFetcher())

    news = await collector.fetch(rss_source(MAIN_FEED, SECTION_FEED))

    assert [item.raw["feed_url"] for item in news] == [MAIN_FEED]


@pytest.mark.asyncio
async def test_a_source_without_feeds_yields_nothing():
    reader = FakeFeedReader({})
    collector = RssCollector(reader, UnreachablePageFetcher())

    assert await collector.fetch(rss_source()) == []
    assert reader.read_urls == []
