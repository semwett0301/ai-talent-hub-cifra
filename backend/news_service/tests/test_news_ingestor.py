import uuid
from datetime import UTC, datetime

import pytest
from common.entities.news import NewsDTO, SourceType
from common.entities.source import SourceReliability
from news_service.application.errors import NewsProcessingError, SummaryEmbeddingError
from news_service.application.services.news_ingestor import NewsIngestor
from news_service.domain.event_summary import EventSummary, PreparedNews, StoredNewsState


def _news(url: str) -> NewsDTO:
    return NewsDTO(
        source_id=uuid.uuid4(),
        source_link="https://source.test",
        source_name="Source Test",
        source_type=SourceType.WEB,
        source_reliability=SourceReliability.MEDIUM,
        url=url,
        title="Acme launched a product",
        text="Acme launched a product.",
        published_at=datetime(2026, 9, 5, tzinfo=UTC),
    )


class _Repository:
    def __init__(self, events: list[str], states=None) -> None:
        self.events = events
        self.states = states or {}
        self.saved: list[PreparedNews] = []
        self.pending: list[EventSummary] = []
        self.unembedded: list[EventSummary] = []

    async def list_states(self, urls):
        self.events.append("states")
        return self.states

    async def save_summaries(self, items):
        self.events.append("save")
        self.saved = items
        self.unembedded = [prepared.summary for prepared in items]

    async def list_unembedded(self, urls):
        self.events.append("unembedded")
        return self.unembedded

    async def save_embeddings(self, summaries):
        self.events.append("save_embeddings")
        self.pending = summaries

    async def list_pending(self, urls):
        self.events.append("pending")
        return self.pending


class _Models:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls = 0

    async def summarize(self, targets):
        self.events.append("summarize")
        self.calls += 1
        return [
            EventSummary(
                target.news_id,
                target.news.url,
                "Acme launched a product",
                True,
                target.news.published_at,
            )
            for target in targets
        ]


class _Embedder:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls = 0

    def embed(self, summaries):
        self.events.append("embed")
        self.calls += 1
        return [[1.0] for _ in summaries]


class _FailingEmbedder(_Embedder):
    def embed(self, summaries):
        self.events.append("embed")
        raise SummaryEmbeddingError("failed")


class _Stage:
    def __init__(self, events: list[str], name: str) -> None:
        self.events = events
        self.name = name
        self.processed: list[str] = []

    async def process(self, urls):
        self.events.append(self.name)
        self.processed = urls


@pytest.mark.asyncio
async def test_batch_is_fully_summarized_and_saved_before_deduplication():
    events: list[str] = []
    repository = _Repository(events)
    models = _Models(events)
    embedder = _Embedder(events)
    deduplicator = _Stage(events, "dedup")
    ranker = _Stage(events, "ranking")
    ingestor = NewsIngestor(
        repository,
        models,
        embedder,
        (deduplicator, ranker),  # type: ignore[arg-type]
    )

    inserted = await ingestor.handle_batch([_news("https://news.test/1")])

    assert inserted == 1
    assert events == [
        "states",
        "summarize",
        "save",
        "unembedded",
        "embed",
        "save_embeddings",
        "dedup",
        "ranking",
    ]
    assert repository.pending[0].embedding == (1.0,)


@pytest.mark.asyncio
async def test_retry_reuses_saved_summary_and_only_resumes_deduplication():
    events: list[str] = []
    news_id = uuid.uuid4()
    states = {"https://news.test/1": StoredNewsState(news_id, has_summary=True)}
    repository = _Repository(events, states)
    repository.pending = [
        EventSummary(
            news_id,
            "https://news.test/1",
            "saved summary",
            True,
            datetime(2026, 9, 5, tzinfo=UTC),
            (1.0,),
        )
    ]
    repository.unembedded = []
    models = _Models(events)
    embedder = _Embedder(events)
    deduplicator = _Stage(events, "dedup")
    ranker = _Stage(events, "ranking")
    ingestor = NewsIngestor(
        repository,
        models,
        embedder,
        (deduplicator, ranker),  # type: ignore[arg-type]
    )

    inserted = await ingestor.handle_batch([_news("https://news.test/1")])

    assert inserted == 0
    assert events == ["states", "unembedded", "dedup", "ranking"]
    assert models.calls == 0
    assert embedder.calls == 0


@pytest.mark.asyncio
async def test_embedding_failure_happens_after_summary_is_persisted():
    events: list[str] = []
    repository = _Repository(events)
    ingestor = NewsIngestor(
        repository,
        _Models(events),
        _FailingEmbedder(events),
        (_Stage(events, "dedup"), _Stage(events, "ranking")),  # type: ignore[arg-type]
    )

    with pytest.raises(NewsProcessingError):
        await ingestor.handle_batch([_news("https://news.test/1")])

    assert events == ["states", "summarize", "save", "unembedded", "embed"]
    assert repository.saved[0].summary.text == "Acme launched a product"


@pytest.mark.asyncio
async def test_repeated_url_inside_batch_is_summarized_once():
    events: list[str] = []
    repository = _Repository(events)
    models = _Models(events)
    ingestor = NewsIngestor(
        repository,
        models,
        _Embedder(events),
        (_Stage(events, "dedup"), _Stage(events, "ranking")),  # type: ignore[arg-type]
    )

    inserted = await ingestor.handle_batch(
        [_news("https://news.test/1"), _news("https://news.test/1")]
    )

    assert inserted == 1
    assert len(repository.saved) == 1
