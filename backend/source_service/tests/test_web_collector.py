from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from domain.entities.news import SourceType
from domain.entities.source import SourceReliability
from domain.schemas import Source
from source_service.application.web_crawl.models import ArticleRecord
from source_service.application.web_crawl.settings import RuntimeSettings
from source_service.infrastructure.collectors.web import WebCrawlCollector


class FakePipeline:
    received_config = None
    received_crawler = None

    def __init__(self, config, crawler) -> None:
        type(self).received_config = config
        type(self).received_crawler = crawler

    async def run(self):
        return [
            ArticleRecord(
                url="https://example.test/news/release",
                canonical_url="https://example.test/news/release",
                source_site="Example",
                source_hub="https://example.test/news",
                title="Important release",
                published_at=datetime(2026, 9, 4, 10, tzinfo=ZoneInfo("Europe/Moscow")),
                modified_at=datetime(2026, 9, 4, 11, tzinfo=ZoneInfo("Europe/Moscow")),
                author="Editorial team",
                section="News",
                language="en",
                description="A description",
                image_url="https://example.test/image.png",
                text="The complete article text.",
                word_count=4,
                fetched_at=datetime(2026, 9, 4, 12, tzinfo=ZoneInfo("Europe/Moscow")),
                date_source="json_ld",
                date_confidence=1.0,
                date_evidence="datePublished",
                metadata={"crawler_metadata": {"og:type": "article"}},
            )
        ]


class FakeCrawler:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_web_collector_adapts_full_agent_record_to_news_contract():
    source = Source(
        name="Example",
        link="https://example.test",
        type=SourceType.WEB,
        reliability=SourceReliability.HIGH,
    )
    collector = WebCrawlCollector(
        runtime=RuntimeSettings(
            days=7,
            max_article_candidates_per_site=12,
            llm_date_fallback=False,
        ),
        crawler_factory=FakeCrawler,
        pipeline_factory=FakePipeline,
    )

    items = await collector.fetch(source)

    assert len(items) == 1
    item = items[0]
    assert item.source_type is SourceType.WEB
    assert item.source_link == source.link
    assert item.url == "https://example.test/news/release"
    assert item.text == "The complete article text."
    assert item.published_at == datetime(2026, 9, 4, 10, tzinfo=ZoneInfo("Europe/Moscow"))
    assert item.raw["title"] == "Important release"
    assert item.raw["author"] == "Editorial team"
    assert item.raw["article"]["metadata"]["crawler_metadata"]["og:type"] == "article"
    assert item.raw["article"]["fetched_at"] == "2026-09-04T12:00:00+03:00"
    assert FakePipeline.received_config.settings.days == 7
    assert FakePipeline.received_config.settings.max_article_candidates_per_site == 12
    assert FakePipeline.received_config.settings.llm_date_fallback is False
