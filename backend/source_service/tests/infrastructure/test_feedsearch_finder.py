from dataclasses import dataclass

from source_service.infrastructure.parsing.feedsearch_finder import _rss_feed_urls

RSS_URL = "https://example.test/rss.xml"
SECTION_RSS_URL = "https://example.test/news/rss"
ATOM_URL = "https://example.test/atom.xml"


@dataclass(frozen=True)
class DiscoveredFeed:
    url: str | None
    version: str


def test_keeps_rss_feeds_only_in_score_order():
    feeds = [
        DiscoveredFeed(RSS_URL, "rss20"),
        DiscoveredFeed(ATOM_URL, "atom10"),
        DiscoveredFeed(SECTION_RSS_URL, "rss20"),
    ]

    assert _rss_feed_urls(feeds) == [RSS_URL, SECTION_RSS_URL]


def test_lists_a_feed_url_once():
    feeds = [DiscoveredFeed(RSS_URL, "rss20"), DiscoveredFeed(RSS_URL, "rss091")]

    assert _rss_feed_urls(feeds) == [RSS_URL]


def test_skips_a_feed_without_an_address():
    assert _rss_feed_urls([DiscoveredFeed(None, "rss20")]) == []
