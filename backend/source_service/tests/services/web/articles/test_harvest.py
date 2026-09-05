from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from common.core.settings import WebCrawlSettings
from source_service.application.dto.crawl_run import CrawlRun
from source_service.application.services.web.articles import ArticleHarvest
from source_service.domain import Article, ArticleContent, ArticleStatus, PublicationDate

MOSCOW = ZoneInfo("Europe/Moscow")


def dated(url: str, published_at: datetime) -> Article:
    content = ArticleContent(
        final_url=url,
        title="Title",
        text="x " * 100,
        word_count=100,
        fetched_at=datetime.now(MOSCOW),
    )
    publication = PublicationDate(value=published_at, source="json_ld", confidence=0.99)
    return Article(url=url).with_content(content).with_publication(publication)


class FakeFetching:
    """Returns every candidate `DATED` with one and the same printed date."""

    def __init__(self, published_at: datetime):
        self.published_at = published_at
        self.batches: list[list[str]] = []

    async def choose_container(self, url):
        return None

    async def run(self, articles, selector):
        self.batches.append([a.url for a in articles])
        return [dated(a.url, self.published_at) for a in articles]


def harvest(fetching: FakeFetching, settings: WebCrawlSettings) -> ArticleHarvest:
    return ArticleHarvest(fetching, settings)  # type: ignore[arg-type]


def candidates(count: int) -> list[Article]:
    return [Article(url=f"https://example.test/news/{i}") for i in range(count)]


@pytest.mark.asyncio
async def test_stops_after_consecutive_batches_of_reliably_old_dates():
    settings = WebCrawlSettings(
        article_batch_size=2,
        out_of_scope_consecutive_batches=2,
        out_of_scope_min_resolved_dates_per_batch=2,
    )
    fetching = FakeFetching(datetime.now(MOSCOW) - timedelta(days=30))
    stats = CrawlRun(site="example.test")

    fetched = await harvest(fetching, settings).run(candidates(10), stats)

    assert len(fetching.batches) == 2
    assert len(fetched) == 4
    assert stats.stopped_early is True


@pytest.mark.asyncio
async def test_a_batch_with_too_few_dates_never_counts_as_old():
    settings = WebCrawlSettings(
        article_batch_size=2,
        out_of_scope_consecutive_batches=2,
        out_of_scope_min_resolved_dates_per_batch=3,
    )
    fetching = FakeFetching(datetime.now(MOSCOW) - timedelta(days=30))
    stats = CrawlRun(site="example.test")

    await harvest(fetching, settings).run(candidates(6), stats)

    assert len(fetching.batches) == 3
    assert stats.stopped_early is False


@pytest.mark.asyncio
async def test_fresh_pages_flow_through_every_batch():
    settings = WebCrawlSettings(article_batch_size=2)
    fetching = FakeFetching(datetime.now(MOSCOW))
    stats = CrawlRun(site="example.test")

    fetched = await harvest(fetching, settings).run(candidates(5), stats)

    assert len(fetched) == 5
    assert all(a.status is ArticleStatus.DATED for a in fetched)
    assert len(fetching.batches) == 3
    assert stats.stopped_early is False
    assert stats.fetched == 5


@pytest.mark.asyncio
async def test_no_candidates_fetches_nothing():
    fetching = FakeFetching(datetime.now(MOSCOW))

    fetched = await harvest(fetching, WebCrawlSettings()).run([], CrawlRun(site="example.test"))

    assert fetched == []
    assert fetching.batches == []
