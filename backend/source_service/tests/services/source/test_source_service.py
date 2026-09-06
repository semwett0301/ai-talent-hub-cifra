import uuid

import pytest
from common.core.settings import SourceSchedulerSettings
from common.entities.news import SourceType
from common.schemas import Source
from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.errors import SourceNotRelevantError
from source_service.application.ports.source import SourceRepository
from source_service.application.services.source import SourceService
from source_service.domain.urls import source_identity

TELEGRAM_LINK = "https://t.me/example"
FEEDS = ["https://example.test/rss.xml", "https://example.test/news/feed"]
DEFAULT_INTERVAL = 300
FEEDS_LIMIT = 3
CUSTOM_INTERVAL = 86400


def source(
    *, link: str = "https://example.test", relevant: bool = True, interval: int | None = None
) -> Source:
    return Source(
        id=uuid.uuid4(),
        name="Example",
        link=link,
        normalized_link=source_identity(link),
        type=SourceType.WEB,
        is_enabled=False,
        is_relevant=relevant,
        poll_interval_seconds=interval,
    )


class FakeRepo(SourceRepository):
    def __init__(self) -> None:
        self.created: dict = {}
        self.feed_urls: list[str] | None = None
        self.rows: list[Source] = []

    async def list_all(self) -> list[Source]:
        return self.rows

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]:
        return [row for row in self.rows if row.is_enabled]

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return next((row for row in self.rows if row.id == source_id), None)

    async def create(self, data: dict, feed_urls: list[str]) -> Source:
        self.created = data
        self.feed_urls = feed_urls
        return Source(id=uuid.uuid4(), **data)

    async def update(self, src: Source, data: dict, feed_urls: list[str] | None = None) -> Source:
        for key, value in data.items():
            setattr(src, key, value)
        self.feed_urls = feed_urls
        return src

    async def delete(self, src: Source) -> None:
        self.rows.remove(src)


class FakeRegistry:
    def __init__(self) -> None:
        self.registered: list[Source] = []

    async def register(self, src: Source) -> None:
        self.registered.append(src)


class FakeFeedFinder:
    def __init__(self, feeds: list[str] | None = None) -> None:
        self.calls: list[str] = []
        self.feeds = feeds or []

    async def find(self, url: str) -> list[str]:
        self.calls.append(url)
        return self.feeds


def build(feeds=None):
    repo, finder = FakeRepo(), FakeFeedFinder(feeds)
    settings = SourceSchedulerSettings(
        source_poll_interval_seconds=DEFAULT_INTERVAL, source_rss_feeds_limit=FEEDS_LIMIT
    )
    return SourceService(repo, FakeRegistry(), finder, settings), repo, finder


@pytest.mark.asyncio
async def test_create_derives_type_and_normalized_link():
    service, repo, finder = build()

    created = await service.create(SourceCreate(name="Example", link="https://WWW.Example.test/"))

    assert created.type == SourceType.WEB
    assert repo.created["normalized_link"] == "https://example.test/"
    assert finder.calls == ["https://WWW.Example.test/"]


@pytest.mark.asyncio
async def test_create_stores_every_feed_the_finder_returns():
    service, repo, _ = build(feeds=FEEDS)

    created = await service.create(SourceCreate(name="Example", link="https://example.test"))

    assert created.type == SourceType.RSS
    assert repo.feed_urls == FEEDS


@pytest.mark.asyncio
async def test_create_keeps_only_the_best_ranked_feeds_up_to_the_limit():
    found = [f"https://example.test/feed-{index}" for index in range(FEEDS_LIMIT + 2)]
    service, repo, _ = build(feeds=found)

    await service.create(SourceCreate(name="Example", link="https://example.test"))

    assert repo.feed_urls == found[:FEEDS_LIMIT]


@pytest.mark.asyncio
async def test_create_stores_no_feeds_for_a_web_source():
    service, repo, _ = build()

    await service.create(SourceCreate(name="Example", link="https://example.test"))

    assert repo.feed_urls == []


@pytest.mark.asyncio
async def test_create_detects_telegram_without_fetching():
    service, repo, finder = build()

    created = await service.create(SourceCreate(name="Channel", link=TELEGRAM_LINK))

    assert created.type == SourceType.TELEGRAM
    assert finder.calls == []


@pytest.mark.asyncio
async def test_update_recomputes_identity_when_the_link_changes():
    service, _, _ = build()

    updated = await service.update(source(), SourceUpdate(link=TELEGRAM_LINK))

    assert updated.type == SourceType.TELEGRAM
    assert updated.normalized_link == TELEGRAM_LINK


@pytest.mark.asyncio
async def test_update_touches_only_the_fields_that_were_sent():
    service, _, finder = build()
    existing = source()

    updated = await service.update(existing, SourceUpdate(is_enabled=True))

    assert updated.is_enabled
    assert updated.name == "Example"
    assert finder.calls == []


@pytest.mark.asyncio
async def test_update_refuses_to_enable_a_non_relevant_source():
    service, _, _ = build()

    with pytest.raises(SourceNotRelevantError):
        await service.update(source(relevant=False), SourceUpdate(is_enabled=True))


@pytest.mark.asyncio
async def test_create_schedules_a_pull_source_on_the_default_interval():
    service, repo, _ = build()

    await service.create(SourceCreate(name="Example", link="https://example.test"))

    assert repo.created["poll_interval_seconds"] == DEFAULT_INTERVAL


@pytest.mark.asyncio
async def test_create_leaves_a_telegram_source_unscheduled():
    service, repo, _ = build()

    await service.create(SourceCreate(name="Channel", link=TELEGRAM_LINK))

    assert repo.created["poll_interval_seconds"] is None


@pytest.mark.asyncio
async def test_a_new_link_clears_the_crawler_s_irrelevance_verdict():
    service, _, _ = build()

    updated = await service.update(
        source(relevant=False), SourceUpdate(link="https://another.test")
    )

    assert updated.is_relevant
    assert updated.is_enabled


@pytest.mark.asyncio
async def test_a_new_link_leaves_a_source_the_operator_disabled_off():
    service, _, _ = build()

    updated = await service.update(source(), SourceUpdate(link="https://another.test"))

    assert not updated.is_enabled


@pytest.mark.asyncio
async def test_editing_anything_but_the_link_leaves_the_flags_alone():
    service, _, _ = build()

    updated = await service.update(source(relevant=False), SourceUpdate(name="Renamed"))

    assert not updated.is_relevant
    assert not updated.is_enabled


@pytest.mark.asyncio
async def test_a_link_change_keeps_an_interval_the_operator_chose():
    service, _, _ = build()

    updated = await service.update(
        source(interval=CUSTOM_INTERVAL), SourceUpdate(link="https://another.test")
    )

    assert updated.poll_interval_seconds == CUSTOM_INTERVAL


@pytest.mark.asyncio
async def test_becoming_telegram_drops_the_schedule():
    service, _, _ = build()

    updated = await service.update(
        source(interval=CUSTOM_INTERVAL), SourceUpdate(link=TELEGRAM_LINK)
    )

    assert updated.poll_interval_seconds is None


@pytest.mark.asyncio
async def test_resending_the_same_address_does_not_re_detect():
    service, repo, finder = build()
    existing = source(link="https://example.test/")

    await service.update(existing, SourceUpdate(name="Renamed", link="https://WWW.Example.test"))

    assert finder.calls == []
    assert existing.name == "Renamed"
    assert repo.feed_urls is None


@pytest.mark.asyncio
async def test_a_new_link_replaces_the_feed_list():
    service, repo, _ = build(feeds=FEEDS)

    await service.update(source(), SourceUpdate(link="https://another.test"))

    assert repo.feed_urls == FEEDS
