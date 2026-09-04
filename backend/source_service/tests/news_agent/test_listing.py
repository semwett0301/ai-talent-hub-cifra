from datetime import datetime
from zoneinfo import ZoneInfo

from source_service.application.web_crawl.listing import (
    is_pagination_url,
    listing_identity,
    listing_links,
    listing_llm_snapshot,
    next_listing_page,
)

HTML = """
<main>
  <article><a href="/content/new-story-with-a-long-slug">Fresh important news story</a><time datetime="2026-09-04T12:00:00+03:00">04.09 12:00</time></article>
  <article><a href="/content/old-story-with-a-long-slug">Old important news story</a><time datetime="2026-08-20T12:00:00+03:00">20.08 12:00</time></article>
  <a rel="next" href="?page=1">Дальше</a>
</main>
"""


def test_listing_identity_deduplicates_pagination():
    assert listing_identity("https://example.test/news?page=0") == "https://example.test/news"
    assert is_pagination_url("https://example.test/news?page=1")


def test_listing_links_keep_card_order_and_dates():
    links = listing_links(
        HTML, base_url="https://example.test/news", timezone="Europe/Moscow", score_threshold=0.18
    )
    assert [link.title for link in links] == [
        "Fresh important news story",
        "Old important news story",
    ]
    assert links[0].published_at == datetime(2026, 9, 4, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    assert (
        next_listing_page(HTML, base_url="https://example.test/news")
        == "https://example.test/news?page=1"
    )


def test_listing_llm_snapshot_is_bounded_and_exposes_cards_and_pagination():
    snapshot = listing_llm_snapshot(HTML, base_url="https://example.test/news")
    assert len(snapshot["cards"]) == 2
    assert snapshot["pagination"] == [
        {"url": "https://example.test/news?page=1", "label": "Дальше"}
    ]
    assert len(str(snapshot["page_text"])) <= 1800
