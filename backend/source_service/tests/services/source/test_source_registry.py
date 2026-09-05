import uuid
from typing import Any

import pytest
from common.core.settings import SourceSchedulerSettings
from common.entities.news import SourceType
from common.schemas import Source
from source_service.application.ports.source import PullRun
from source_service.application.services.source import SourceCollectors, SourceRegistry

DEFAULT_INTERVAL = 300


def source(*, enabled: bool = True, interval: int | None = None) -> Source:
    return Source(
        id=uuid.uuid4(),
        name="Example",
        link="https://example.test",
        type=SourceType.RSS,
        is_enabled=enabled,
        poll_interval_seconds=interval,
    )


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: dict[uuid.UUID, int] = {}
        self.runs: dict[uuid.UUID, PullRun] = {}

    def schedule(self, source_id: uuid.UUID, seconds: int, run: PullRun) -> None:
        self.jobs[source_id] = seconds
        self.runs[source_id] = run

    def unschedule(self, source_id: uuid.UUID) -> None:
        self.jobs.pop(source_id, None)


class FakePull:
    def __init__(self, items: list[Any]) -> None:
        self.items = items
        self.fetched: list[Source] = []

    async def fetch(self, src: Source) -> list[Any]:
        self.fetched.append(src)
        return self.items


class FakePush:
    def __init__(self) -> None:
        self.subscribed: list[Source] = []
        self.unsubscribed: list[Source] = []

    async def subscribe(self, src: Source) -> None:
        self.subscribed.append(src)

    async def unsubscribe(self, src: Source) -> None:
        self.unsubscribed.append(src)


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[Any] = []

    async def publish_news(self, items: list[Any]) -> int:
        self.published += items
        return len(items)


class FakeRepo:
    def __init__(self, rows: list[Source]) -> None:
        self.rows = rows

    async def list_enabled(self, source_type: SourceType | None = None) -> list[Source]:
        return [row for row in self.rows if row.is_enabled]

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return next((row for row in self.rows if row.id == source_id), None)


def build(rows: list[Source], pull: FakePull, push: FakePush, publisher: FakePublisher):
    scheduler = FakeScheduler()
    collectors = SourceCollectors(
        pull={SourceType.RSS: pull},  # type: ignore[dict-item]
        push={SourceType.TELEGRAM: push},  # type: ignore[dict-item]
        publisher=publisher,  # type: ignore[arg-type]
    )
    registry = SourceRegistry(
        collectors,
        scheduler,  # type: ignore[arg-type]
        FakeRepo(rows),  # type: ignore[arg-type]
        SourceSchedulerSettings(source_poll_interval_seconds=DEFAULT_INTERVAL),
    )
    return registry, scheduler


@pytest.mark.asyncio
async def test_an_enabled_pull_source_is_scheduled_at_its_own_interval():
    src = source(interval=60)
    registry, scheduler = build([src], FakePull([]), FakePush(), FakePublisher())

    await registry.register(src)

    assert scheduler.jobs == {src.id: 60}


@pytest.mark.asyncio
async def test_a_pull_source_without_an_interval_falls_back_to_the_setting():
    src = source()
    registry, scheduler = build([src], FakePull([]), FakePush(), FakePublisher())

    await registry.register(src)

    assert scheduler.jobs == {src.id: DEFAULT_INTERVAL}


@pytest.mark.asyncio
async def test_registering_a_disabled_pull_source_tears_its_job_down():
    src = source(interval=60)
    registry, scheduler = build([src], FakePull([]), FakePush(), FakePublisher())
    await registry.register(src)

    src.is_enabled = False
    await registry.register(src)

    assert scheduler.jobs == {}


@pytest.mark.asyncio
async def test_the_scheduled_job_fetches_and_publishes():
    src = source(interval=60)
    pull, publisher = FakePull(["one", "two"]), FakePublisher()
    registry, scheduler = build([src], pull, FakePush(), publisher)
    await registry.register(src)

    await scheduler.runs[src.id](src.id)

    assert pull.fetched == [src]
    assert publisher.published == ["one", "two"]


@pytest.mark.asyncio
async def test_a_run_whose_source_was_disabled_meanwhile_collects_nothing():
    src = source(interval=60)
    pull, publisher = FakePull(["one"]), FakePublisher()
    registry, scheduler = build([src], pull, FakePush(), publisher)
    await registry.register(src)

    src.is_enabled = False
    await scheduler.runs[src.id](src.id)

    assert pull.fetched == []
    assert publisher.published == []


@pytest.mark.asyncio
async def test_a_push_source_is_subscribed_and_unsubscribed():
    src = source()
    src.type = SourceType.TELEGRAM
    push = FakePush()
    registry, _ = build([src], FakePull([]), push, FakePublisher())

    await registry.register(src)
    await registry.unregister(src)

    assert push.subscribed == [src]
    assert push.unsubscribed == [src]
