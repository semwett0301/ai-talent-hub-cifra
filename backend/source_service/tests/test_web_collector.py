from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas import Source
from source_service.domain import (
    Article,
    ArticleContent,
    ArticleOrigin,
    PublicationDate,
    Site,
)
from source_service.infrastructure.collectors.web import WebCrawlCollector

MOSCOW = ZoneInfo("Europe/Moscow")


def accepted_article() -> Article:
    content = ArticleContent(
        final_url="https://example.test/news/release",
        canonical_url="https://example.test/news/release",
        title="Important release",
        text="The complete article text.",
        word_count=4,
        author="Editorial team",
        fetched_at=datetime(2026, 9, 4, 12, tzinfo=MOSCOW),
        metadata={"crawler_metadata": {"og:type": "article"}},
    )
    publication = PublicationDate(
        value=datetime(2026, 9, 4, 10, tzinfo=MOSCOW), source="json_ld", confidence=1.0
    )
    discovered = Article(
        url="https://example.test/news/release",
        hub_url="https://example.test/news",
        title_hint="Important release",
        origin=ArticleOrigin.LISTING,
    )
    return discovered.with_content(content).with_publication(publication).accept()


class FakeWebCrawl:
    received_site: Site | None = None

    async def run(self, site: Site) -> list[Article]:
        type(self).received_site = site
        return [accepted_article()]


@pytest.mark.asyncio
async def test_web_collector_turns_the_source_into_a_site_and_accepted_articles_into_news():
    source = Source(
        name="Example",
        link="https://example.test",
        type=SourceType.WEB,
        reliability=SourceReliability.HIGH,
    )
    collector = WebCrawlCollector(FakeWebCrawl())  # type: ignore[arg-type]

    items = await collector.fetch(source)

    assert FakeWebCrawl.received_site == Site(url="https://example.test", name="Example")
    assert len(items) == 1
    item = items[0]
    assert item.source_type is SourceType.WEB
    assert item.url == "https://example.test/news/release"
    assert item.published_at == datetime(2026, 9, 4, 10, tzinfo=MOSCOW)
    assert item.raw["title"] == "Important release"
    assert item.raw["date_source"] == "json_ld"
    assert item.raw["article"]["status"] == "accepted"
