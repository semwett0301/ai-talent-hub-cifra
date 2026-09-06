import uuid

import pytest
from common.entities.news import SourceType
from common.schemas import Source
from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.errors import SourceNotRelevantError
from source_service.application.ports.source import SourceRepository
from source_service.application.services.source import SourceService

TELEGRAM_LINK = "https://t.me/example"


def source(*, link: str = "https://example.test", relevant: bool = True) -> Source:
    return Source(
        id=uuid.uuid4(),
        name="Example",
        link=link,
        normalized_link=link,
        type=SourceType.WEB,
        is_enabled=False,
        is_relevant=relevant,
    )


class FakeRepo(SourceRepository):
    def __init__(self) -> None:
        self.created: dict = {}
        self.rows: list[Source] = []

    async def list_all(self) -> list[Source]:
        return self.rows

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]:
        return [row for row in self.rows if row.is_enabled]

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return next((row for row in self.rows if row.id == source_id), None)

    async def create(self, data: dict) -> Source:
        self.created = data
        return Source(id=uuid.uuid4(), **data)

    async def update(self, src: Source, data: dict) -> Source:
        for key, value in data.items():
            setattr(src, key, value)
        return src

    async def delete(self, src: Source) -> None:
        self.rows.remove(src)


class FakeRegistry:
    def __init__(self) -> None:
        self.registered: list[Source] = []

    async def register(self, src: Source) -> None:
        self.registered.append(src)


class FakeFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def fetch(self, url: str) -> str | None:
        self.calls.append(url)
        return None


def build():
    repo, fetcher = FakeRepo(), FakeFetcher()
    return SourceService(repo, FakeRegistry(), fetcher), repo, fetcher


@pytest.mark.asyncio
async def test_create_derives_type_and_normalized_link():
    service, repo, fetcher = build()

    created = await service.create(SourceCreate(name="Example", link="https://WWW.Example.test/"))

    assert created.type == SourceType.WEB
    assert repo.created["normalized_link"] == "https://example.test/"
    assert fetcher.calls == ["https://WWW.Example.test/"]


@pytest.mark.asyncio
async def test_create_detects_telegram_without_fetching():
    service, repo, fetcher = build()

    created = await service.create(SourceCreate(name="Channel", link=TELEGRAM_LINK))

    assert created.type == SourceType.TELEGRAM
    assert fetcher.calls == []


@pytest.mark.asyncio
async def test_update_recomputes_identity_when_the_link_changes():
    service, _, _ = build()

    updated = await service.update(source(), SourceUpdate(link=TELEGRAM_LINK))

    assert updated.type == SourceType.TELEGRAM
    assert updated.normalized_link == TELEGRAM_LINK


@pytest.mark.asyncio
async def test_update_touches_only_the_fields_that_were_sent():
    service, _, fetcher = build()
    existing = source()

    updated = await service.update(existing, SourceUpdate(is_enabled=True))

    assert updated.is_enabled
    assert updated.name == "Example"
    assert fetcher.calls == []


@pytest.mark.asyncio
async def test_update_refuses_to_enable_a_non_relevant_source():
    service, _, _ = build()

    with pytest.raises(SourceNotRelevantError):
        await service.update(source(relevant=False), SourceUpdate(is_enabled=True))
