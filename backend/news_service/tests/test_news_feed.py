import uuid
from datetime import UTC, datetime

from common.schemas import News
from news_service.application.dto.news import NewsQuery, NewsVisibility
from news_service.application.services import NewsFeed
from news_service.infrastructure.repositories.news_repo import _like_pattern

NEWS_ID = uuid.uuid4()


class FakeRepo:
    def __init__(self, news: News | None) -> None:
        self.news = news
        self.queries: list[NewsQuery] = []
        self.commits = 0

    async def list_matching(self, query: NewsQuery) -> list[News]:
        self.queries.append(query)
        return [self.news] if self.news else []

    async def mark_dismissed(self, news_id: uuid.UUID) -> News | None:
        if self.news is not None and self.news.dismissed_at is None:
            self.news.dismissed_at = datetime(2026, 9, 6, tzinfo=UTC)
        return self.news

    async def mark_restored(self, news_id: uuid.UUID) -> News | None:
        if self.news is not None:
            self.news.dismissed_at = None
        return self.news

    async def commit(self) -> None:
        self.commits += 1


def feed(news: News | None) -> tuple[NewsFeed, FakeRepo]:
    repo = FakeRepo(news)
    return NewsFeed(repo), repo  # type: ignore[arg-type]


async def test_list_passes_the_query_through_and_returns_every_match():
    service, repo = feed(News(id=NEWS_ID, url="https://example.test/a", title="A", text=""))
    query = NewsQuery(q="a", visibility=NewsVisibility.ALL)

    items = await service.list(query)

    assert [item.id for item in items] == [NEWS_ID]
    assert repo.queries == [query]


async def test_dismiss_then_restore_round_trips_the_visibility_and_commits_each():
    service, repo = feed(News(id=NEWS_ID, url="https://example.test/a", title="A", text=""))

    dismissed = await service.dismiss(NEWS_ID)
    assert dismissed is not None and dismissed.dismissed_at is not None

    restored = await service.restore(NEWS_ID)
    assert restored is not None and restored.dismissed_at is None
    assert repo.commits == 2


async def test_unknown_ids_yield_none_without_a_commit():
    service, repo = feed(None)

    assert await service.dismiss(NEWS_ID) is None
    assert await service.restore(NEWS_ID) is None
    assert repo.commits == 0


def test_like_pattern_neutralises_wildcards():
    assert _like_pattern("100%_sure\\") == r"%100\%\_sure\\%"
