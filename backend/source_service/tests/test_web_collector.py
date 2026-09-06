import uuid
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
        description="A short blurb.",
        section="Releases",
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
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.received_source: Source | None = None

    async def run(self, source: Source) -> list[Article]:
        self.received_source = source
        return self.articles


def source() -> Source:
    return Source(
        id=uuid.uuid4(),
        name="Example",
        link="https://example.test",
        type=SourceType.WEB,
        reliability=SourceReliability.HIGH,
    )


@pytest.mark.asyncio
async def test_web_collector_forwards_the_source_and_turns_accepted_articles_into_news():
    crawl = FakeWebCrawl([accepted_article()])
    collector = WebCrawlCollector(crawl)  # type: ignore[arg-type]
    src = source()

    items = await collector.fetch(src)

    assert crawl.received_source is src
    assert len(items) == 1
    item = items[0]
    assert item.source_type is SourceType.WEB
    assert item.url == "https://example.test/news/release"
    assert item.published_at == datetime(2026, 9, 4, 10, tzinfo=MOSCOW)
    assert item.source_id == src.id
    assert item.source_name == "Example"
    assert item.title == "Important release"
    assert item.excerpt == "A short blurb."
    assert item.source_tags == ["Releases"]
