from source_service.domain.urls import (
    host_matches,
    is_pagination_url,
    listing_identity,
    normalize_url,
)


def test_normalize_url_strips_tracking_fragment_and_trailing_slash():
    assert (
        normalize_url("https://Example.com/news/?utm_source=x&a=1#top")
        == "https://example.com/news?a=1"
    )
    assert normalize_url("mailto:someone@example.com") == ""


def test_host_matches_seed_host_and_subdomains():
    assert host_matches("https://media.example.com/news/x", [], "https://example.com")
    assert not host_matches("https://evil.test/news/x", [], "https://example.com")


def test_listing_identity_folds_pagination():
    assert listing_identity("https://example.test/news?page=0") == "https://example.test/news"
    assert is_pagination_url("https://example.test/news?page=1")
