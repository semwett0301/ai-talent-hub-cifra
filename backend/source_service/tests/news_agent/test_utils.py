from datetime import datetime
from zoneinfo import ZoneInfo

from source_service.application.web_crawl.date_utils import (
    is_older_than_window,
    is_recent,
    parse_date,
)
from source_service.application.web_crawl.url_utils import (
    article_score,
    host_matches,
    hub_score,
    normalize_url,
)
from source_service.infrastructure.crawlers.crawl4ai_support import is_date_probe_page


def test_normalize_url():
    assert (
        normalize_url("https://Example.com/news/?utm_source=x&a=1#top")
        == "https://example.com/news?a=1"
    )


def test_domain_guard():
    assert host_matches("https://media.example.com/news/x", [], "https://example.com")
    assert not host_matches("https://evil.test/news/x", [], "https://example.com")


def test_hub_and_article_scores():
    assert hub_score("https://example.com/press-center") >= 0.35
    assert (
        article_score("https://example.com/news/2026/09/03/long-important-company-announcement")
        >= 0.35
    )


def test_parse_russian_date_and_recent():
    value = parse_date("3 сентября 2026, 12:30 МСК", "Europe/Moscow")
    assert value is not None
    now = datetime(2026, 9, 4, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    assert is_recent(value, 3, "Europe/Moscow", now=now)
    assert not is_older_than_window(value, 3, "Europe/Moscow", now=now)
    old = parse_date("30 августа 2026", "Europe/Moscow")
    assert old is not None
    assert is_older_than_window(old, 3, "Europe/Moscow", now=now)


def test_date_probe_schedule_starts_at_20_and_repeats_every_20_pages():
    assert not is_date_probe_page(19, 20, 20)
    assert is_date_probe_page(20, 20, 20)
    assert not is_date_probe_page(39, 20, 20)
    assert is_date_probe_page(40, 20, 20)
