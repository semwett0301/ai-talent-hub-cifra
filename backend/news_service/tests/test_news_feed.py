import uuid
from datetime import UTC, datetime

from common.schemas import News, NewsClusterRanking, NewsEventState
from news_service.application.dto.news import NewsOut, NewsQuery, NewsVisibility
from news_service.application.services import NewsFeed
from news_service.infrastructure.repositories.news_repo import _feed_statement, _like_pattern
from sqlalchemy.dialects import postgresql

NEWS_ID = uuid.uuid4()
CLUSTER_ID = uuid.uuid4()


IMPACT = {
    "finance_score": 2,
    "finance_reason": "Procurement terms change.",
    "reputation_score": 0,
    "reputation_reason": "Not mentioned.",
    "technology_score": 1,
    "technology_reason": "A new standard is drafted.",
    "competition_score": 0,
    "competition_reason": "No competitor named.",
    "urgency_basis": "within_4_30_days",
    "urgency_reason": "Comments close in two weeks.",
}


def stored_news(
    state: NewsEventState | None = None, ranking: NewsClusterRanking | None = None
) -> News:
    return News(
        id=NEWS_ID,
        schema_version=1,
        source_id=uuid.uuid4(),
        source_link="https://example.test",
        source_name="Example",
        source_type="rss",
        source_reliability="medium",
        source_tags=[],
        url="https://example.test/a",
        title="A",
        text="",
        excerpt=None,
        published_at=None,
        updated_at=None,
        dismissed_at=None,
        is_alert=False,
        created_at=datetime(2026, 9, 6, tzinfo=UTC),
        event_state=state,
        cluster_ranking=ranking,
    )


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


def test_feed_statement_keeps_only_cluster_heads_and_undeduplicated_items():
    sql = str(_feed_statement(NewsQuery()).compile(dialect=postgresql.dialect()))

    assert "LEFT OUTER JOIN news_event_state" in sql
    assert (
        "news_event_state.event_cluster_id IS NULL OR news_event_state.event_cluster_id = news.id"
    ) in sql


def test_feed_statement_shows_only_ranked_relevant_clusters():
    sql = str(_feed_statement(NewsQuery()).compile(dialect=postgresql.dialect()))

    assert "LEFT OUTER JOIN news_cluster_ranking" in sql
    assert "news_cluster_ranking.category IN (" in sql


def test_alerts_tab_is_not_gated_by_relevance():
    sql = str(_feed_statement(NewsQuery(is_alert=True)).compile(dialect=postgresql.dialect()))

    assert "news.is_alert IS true" in sql
    assert "news_cluster_ranking.category IN (" not in sql


def test_news_out_reads_dedup_state_through_the_row():
    state = NewsEventState(news_id=NEWS_ID, summary="Short", event_cluster_id=CLUSTER_ID)

    with_state = NewsOut.model_validate(stored_news(state))
    without_state = NewsOut.model_validate(stored_news())

    assert (with_state.summary, with_state.event_cluster_id) == ("Short", CLUSTER_ID)
    assert (without_state.summary, without_state.event_cluster_id) == (None, None)
    assert without_state.relevance is None


def test_news_out_flattens_the_cluster_ranking_into_relevance():
    ranking = NewsClusterRanking(
        cluster_id=NEWS_ID,
        relevance_score=67.5,
        category="важно",
        member_count=3,
        details={"components": {}, "impact": IMPACT, "bm25_score": 1.0},
    )

    relevance = NewsOut.model_validate(stored_news(ranking=ranking)).relevance

    assert relevance is not None
    assert (relevance.score, relevance.category, relevance.member_count) == (67.5, "важно", 3)
    assert (relevance.urgency_basis, relevance.urgency_reason) == (
        "within_4_30_days",
        "Comments close in two weeks.",
    )
    assert [(reason.dimension, reason.score) for reason in relevance.impact] == [
        ("finance", 2),
        ("reputation", 0),
        ("technology", 1),
        ("competition", 0),
    ]
    assert relevance.impact[0].reason == "Procurement terms change."
