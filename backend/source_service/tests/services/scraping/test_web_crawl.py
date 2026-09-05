from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from common.core.settings import WebCrawlSettings
from common.schemas import Source
from source_service.application.services.article import ArticleJudgement, DateResolution
from source_service.application.services.scraping import WebCrawl
from source_service.application.services.scraping.web_crawl import CrawlStages
from source_service.domain import (
    Article,
    ArticleContent,
    ArticleStatus,
    Hub,
    HubOrigin,
    PublicationDate,
)

MOSCOW = ZoneInfo("Europe/Moscow")
SOURCE = Source(link="https://example.test", name="Example")


def dated_article(url: str, published_at: datetime) -> Article:
    content = ArticleContent(
        final_url=url,
        title="Title",
        text="x " * 100,
        word_count=100,
        fetched_at=datetime.now(MOSCOW),
    )
    publication = PublicationDate(value=published_at, source="json_ld", confidence=0.99)
    return Article(url=url).with_content(content).with_publication(publication)


class FakeHubs:
    async def run(self, site):
        return [Hub.build(site.seed, HubOrigin.SEED)]


class FakeCards:
    def __init__(self, count: int):
        self.count = count

    async def run(self, hubs):
        return [Article(url=f"https://example.test/news/{i}") for i in range(self.count)]


class FakeFetching:
    def __init__(self, published_at: datetime):
        self.published_at = published_at
        self.batches: list[list[str]] = []

    async def choose_container(self, url):
        return None

    async def run(self, articles, selector):
        self.batches.append([a.url for a in articles])
        return [dated_article(a.url, self.published_at) for a in articles]


class FakeSourceRepo:
    def __init__(self) -> None:
        self.updates: list[tuple[Source, dict]] = []

    async def update(self, source: Source, data: dict) -> Source:
        self.updates.append((source, data))
        return source


def crawl(
    fetching: FakeFetching,
    settings: WebCrawlSettings,
    cards: int = 5,
    repo: FakeSourceRepo | None = None,
) -> WebCrawl:
    stages = CrawlStages(
        hubs=FakeHubs(),  # type: ignore[arg-type]
        cards=FakeCards(cards),  # type: ignore[arg-type]
        fetching=fetching,  # type: ignore[arg-type]
        dates=DateResolution(None, settings),
        judgement=ArticleJudgement(settings),
    )
    return WebCrawl(stages, settings, repo or FakeSourceRepo())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_stops_after_a_full_batch_of_reliably_old_dates():
    settings = WebCrawlSettings(
        article_batch_size=2,
        stop_on_out_of_scope_batches=True,
        out_of_scope_consecutive_batches=1,
        out_of_scope_min_resolved_dates_per_batch=2,
    )
    fetching = FakeFetching(datetime.now(MOSCOW) - timedelta(days=30))

    articles = await crawl(fetching, settings).run(SOURCE)

    assert articles == []
    assert fetching.batches == [["https://example.test/news/0", "https://example.test/news/1"]]


@pytest.mark.asyncio
async def test_fresh_articles_flow_through_every_batch_and_come_back_newest_first():
    settings = WebCrawlSettings(article_batch_size=2)
    fetching = FakeFetching(datetime.now(MOSCOW))

    articles = await crawl(fetching, settings).run(SOURCE)

    assert len(articles) == 5
    assert all(a.status is ArticleStatus.ACCEPTED for a in articles)
    assert len(fetching.batches) == 3


@pytest.mark.asyncio
async def test_no_candidates_marks_source_not_relevant():
    settings = WebCrawlSettings()
    fetching = FakeFetching(datetime.now(MOSCOW))
    repo = FakeSourceRepo()

    articles = await crawl(fetching, settings, cards=0, repo=repo).run(SOURCE)

    assert articles == []
    assert fetching.batches == []
    assert repo.updates == [(SOURCE, {"is_relevant": False, "is_enabled": False})]
