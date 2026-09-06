import uuid
from datetime import UTC, datetime, timedelta

import pytest
from common.core.settings import NewsDedupSettings
from news_service.application.services.news_deduplicator import NewsDeduplicator
from news_service.domain.dedup import (
    CandidateCluster,
    ClusterAssignment,
    EventSummary,
    MembershipDecision,
    Precluster,
)


def _summary(news_id: uuid.UUID, hour: int = 10) -> EventSummary:
    return EventSummary(
        news_id,
        f"https://news.test/{news_id}",
        "Acme launched a product",
        {
            "primary_event_found": True,
            "event_time": {"start": "2026-09-05", "precision": "day"},
        },
        datetime(2026, 9, 5, hour, tzinfo=UTC),
        (1.0, 0.0),
    )


class _Repository:
    def __init__(self, first: EventSummary) -> None:
        self.first = first
        self.pending: list[EventSummary] = []
        self.assignments: list[ClusterAssignment] = []
        self.query_count = 0

    async def list_pending(self, urls):
        return self.pending

    async def find_candidates(self, query):
        self.query_count += 1
        if not query.available_pending_ids:
            return []
        return [CandidateCluster(self.first.news_id, 0.9, (self.first,))]

    async def assign_clusters(self, assignments):
        self.assignments = assignments


class _Models:
    def __init__(self, decision: str) -> None:
        self.decision = decision
        self.preclusters: list[Precluster] = []

    async def align(self, preclusters):
        self.preclusters = preclusters
        return [
            {
                summary.news_id: MembershipDecision(self.decision)  # type: ignore[arg-type]
                for summary in precluster.candidates
            }
            for precluster in preclusters
        ]


@pytest.mark.asyncio
async def test_proven_same_member_joins_the_earlier_batch_cluster():
    first = _summary(uuid.uuid4())
    second = _summary(uuid.uuid4(), 11)
    repository = _Repository(first)
    models = _Models("SAME")
    deduplicator = NewsDeduplicator(
        repository,
        models,
        NewsDedupSettings(),  # type: ignore[arg-type]
    )
    repository.pending = [second, first]

    await deduplicator.process([first.url, second.url])

    assert [assignment.cluster_id for assignment in repository.assignments] == [
        first.news_id,
        first.news_id,
    ]
    assert len(models.preclusters) == 1


@pytest.mark.asyncio
async def test_uncertain_member_gets_an_isolated_cluster():
    first = _summary(uuid.uuid4())
    second = _summary(uuid.uuid4(), 11)
    repository = _Repository(first)
    deduplicator = NewsDeduplicator(
        repository,
        _Models("UNCERTAIN"),
        NewsDedupSettings(),  # type: ignore[arg-type]
    )
    repository.pending = [first, second]

    await deduplicator.process([first.url, second.url])

    assert repository.assignments[1].cluster_id == second.news_id


@pytest.mark.asyncio
async def test_explicit_time_conflict_skips_the_llm_and_blocks_merge():
    first = _summary(uuid.uuid4())
    second = _summary(uuid.uuid4(), 11)
    second = EventSummary(
        second.news_id,
        second.url,
        second.text,
        {
            "primary_event_found": True,
            "event_time": {"start": "2026-09-09", "precision": "day"},
        },
        first.published_at + timedelta(hours=1),  # type: ignore[operator]
        second.embedding,
    )
    repository = _Repository(first)
    models = _Models("SAME")
    deduplicator = NewsDeduplicator(
        repository,
        models,
        NewsDedupSettings(),  # type: ignore[arg-type]
    )
    repository.pending = [first, second]

    await deduplicator.process([first.url, second.url])

    assert repository.assignments[1].cluster_id == second.news_id
    assert models.preclusters == []
