from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from source_service.domain import Article, ArticleContent, PublicationDate, merge_duplicates

MOSCOW = ZoneInfo("Europe/Moscow")


def dated(url: str, canonical: str | None, published_at: datetime) -> Article:
    content = ArticleContent(
        final_url=url,
        canonical_url=canonical,
        title="T",
        text="x",
        word_count=1,
        fetched_at=published_at,
    )
    return (
        Article(url=url)
        .with_content(content)
        .with_publication(PublicationDate(value=published_at, source="json_ld", confidence=1.0))
    )


def test_same_canonical_collapses_and_the_newer_version_wins_newest_first():
    now = datetime(2026, 9, 4, 12, tzinfo=MOSCOW)
    older = dated("https://example.test/a?x=1", "https://example.test/a", now - timedelta(hours=2))
    newer = dated("https://example.test/a", "https://example.test/a", now)
    other = dated("https://example.test/b", None, now - timedelta(days=1))

    merged = merge_duplicates([older, other, newer])

    assert [a.url for a in merged] == ["https://example.test/a", "https://example.test/b"]
    assert merged[0].publication is not None and merged[0].publication.value == now
