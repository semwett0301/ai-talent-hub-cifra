from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from domain.core.settings import Settings
from domain.entities.news import SourceType
from domain.entities.source import SourceReliability
from domain.schemas import Source
from source_service.infrastructure.collectors.web import WebCrawlCollector
from source_service.infrastructure.crawlers.news_agent.models import ArticleRecord


class FakePipeline:
    received_config = None
    received_env = None

    def __init__(self, config, env) -> None:
        type(self).received_config = config
        type(self).received_env = env

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


@pytest.mark.asyncio
async def test_web_collector_adapts_full_agent_record_to_news_contract():
    source = Source(
        name="Example",
        link="https://example.test",
        type=SourceType.WEB,
        reliability=SourceReliability.HIGH,
    )
    collector = WebCrawlCollector(
        config=Settings(web_crawl_days=7, web_crawl_max_articles=12, web_crawl_llm_enabled=False),
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
