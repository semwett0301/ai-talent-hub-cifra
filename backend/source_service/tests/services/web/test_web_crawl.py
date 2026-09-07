from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from common.schemas import Source
from source_service.application.services.dedup import StoredNewsFilter
from source_service.application.services.web import CrawlStages, WebCrawl
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


def accepted_article(url: str, canonical: str, published_at: datetime) -> Article:
    content = ArticleContent(
        final_url=url,
        canonical_url=canonical,
        title="Title",
        text="x " * 100,
        word_count=100,
        fetched_at=datetime.now(MOSCOW),
    )
    publication = PublicationDate(value=published_at, source="json_ld", confidence=0.99)
    return Article(url=url).with_content(content).with_publication(publication).accept()


class FakeHubs:
    async def run(self, site):
        return [Hub.build(site.seed, HubOrigin.SEED)]


class FakeCards:
    def __init__(self, count: int):
        self.count = count

    async def run(self, hubs):
        return [Article(url=f"https://example.test/news/{i}") for i in range(self.count)]


class FakeHarvest:
    """Stands in for the whole download stage: hands back a ready list of articles."""

    def __init__(self, fetched: list[Article]):
        self.fetched = fetched
        self.received: list[Article] = []

    async def run(self, candidates, stats):
        self.received = candidates
        return self.fetched


class FakeJudgement:
    """Every article is already accepted — hand the list straight back."""

    def run(self, articles):
        return articles


class FakeSourceRepo:
    def __init__(self) -> None:
        self.updates: list[tuple[Source, dict]] = []

    async def update(self, source: Source, data: dict) -> Source:
        self.updates.append((source, data))
        return source


class FakeStoredNewsIndex:
    def __init__(self, *stored: str) -> None:
        self.stored = set(stored)

    async def list_stored_urls(self, urls: list[str]) -> set[str]:
        return self.stored.intersection(urls)


class FakeDates:
    """Nothing is `FETCHED`, so date resolution has no work to do."""

    async def run(self, articles):
        return articles


def crawl(harvest: FakeHarvest, cards: int, repo: FakeSourceRepo, *stored: str) -> WebCrawl:
    stages = CrawlStages(
        hubs=FakeHubs(),  # type: ignore[arg-type]
        cards=FakeCards(cards),  # type: ignore[arg-type]
        harvest=harvest,  # type: ignore[arg-type]
        dates=FakeDates(),  # type: ignore[arg-type]
        judgement=FakeJudgement(),  # type: ignore[arg-type]
    )
    stored_news = StoredNewsFilter(FakeStoredNewsIndex(*stored), "web")
    return WebCrawl(stages, repo, stored_news)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_no_candidates_marks_source_not_relevant():
    articles = FakeHarvest([])
    repo = FakeSourceRepo()

    found = await crawl(articles, cards=0, repo=repo).run(SOURCE)

    assert found == []
    assert articles.received == []
    assert repo.updates == [(SOURCE, {"is_relevant": False, "is_enabled": False})]


@pytest.mark.asyncio
async def test_harvested_articles_are_deduped_by_identity_and_returned_newest_first():
    canonical = "https://example.test/news/release"
    older = accepted_article(canonical, canonical, datetime(2026, 9, 1, tzinfo=MOSCOW))
    newer = accepted_article(
        "https://example.test/2026/09/release", canonical, datetime(2026, 9, 4, tzinfo=MOSCOW)
    )
    other = accepted_article(
        "https://example.test/news/other",
        "https://example.test/news/other",
        datetime(2026, 9, 3, tzinfo=MOSCOW),
    )
    repo = FakeSourceRepo()

    found = await crawl(FakeHarvest([older, other, newer]), cards=3, repo=repo).run(SOURCE)

    assert [a.url for a in found] == [newer.url, other.url]
    assert all(a.status is ArticleStatus.ACCEPTED for a in found)
    assert repo.updates == []


@pytest.mark.asyncio
async def test_a_stored_candidate_is_dropped_before_harvest():
    harvest = FakeHarvest([])
    repo = FakeSourceRepo()
    stored = "https://example.test/news/0"

    await crawl(harvest, 2, repo, stored).run(SOURCE)

    assert [a.url for a in harvest.received] == ["https://example.test/news/1"]
    assert repo.updates == []


@pytest.mark.asyncio
async def test_every_candidate_already_stored_touches_no_harvest():
    harvest = FakeHarvest([])
    repo = FakeSourceRepo()
    stored = "https://example.test/news/0"

    found = await crawl(harvest, 1, repo, stored).run(SOURCE)

    assert found == []
    assert harvest.received == []
    assert repo.updates == []
