import uuid
from datetime import UTC, datetime

import pytest
from common.entities.npa import NpaDTO
from common.schemas import News
from news_service.application.errors import NpaGatewayError
from news_service.application.services import NpaEscalation

NEWS_ID = uuid.uuid4()


def stored_news() -> News:
    return News(
        id=NEWS_ID,
        url="https://example.test/news/law",
        title="A new law",
        text="The full text.",
        published_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
    )


class FakeRepo:
    def __init__(self, news: News | None) -> None:
        self.news = news
        self.committed = False

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        if self.news is not None:
            self.news.is_alert = True
        return self.news

    async def commit(self) -> None:
        self.committed = True


class FakeGateway:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.received: list[NpaDTO] = []

    async def create(self, act: NpaDTO) -> uuid.UUID:
        if self.error is not None:
            raise self.error
        self.received.append(act)
        return uuid.uuid4()


def escalation(repo: FakeRepo, gateway: FakeGateway) -> NpaEscalation:
    return NpaEscalation(repo, gateway)  # type: ignore[arg-type]


async def test_without_a_body_the_act_is_built_from_the_news_item():
    repo, gateway = FakeRepo(stored_news()), FakeGateway()

    news = await escalation(repo, gateway).escalate(NEWS_ID, None)

    assert news is not None and news.is_alert
    [act] = gateway.received
    assert str(act.url) == "https://example.test/news/law"
    assert act.title == "A new law"
    assert act.text == "The full text."
    assert act.published_at == datetime(2026, 9, 6, 10, tzinfo=UTC)
    assert repo.committed


async def test_an_explicit_body_is_sent_as_is():
    repo, gateway = FakeRepo(stored_news()), FakeGateway()
    act = NpaDTO(url="https://gov.test/act/1", title="Official title")

    await escalation(repo, gateway).escalate(NEWS_ID, act)

    assert gateway.received == [act]


async def test_a_refused_act_is_never_committed():
    repo = FakeRepo(stored_news())
    gateway = FakeGateway(error=NpaGatewayError("npa_service down"))

    with pytest.raises(NpaGatewayError):
        await escalation(repo, gateway).escalate(NEWS_ID, None)

    assert not repo.committed


async def test_an_unknown_id_sends_nothing():
    repo, gateway = FakeRepo(None), FakeGateway()

    assert await escalation(repo, gateway).escalate(NEWS_ID, None) is None
    assert gateway.received == []
    assert not repo.committed
