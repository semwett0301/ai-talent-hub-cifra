from dataclasses import dataclass

import pytest
from source_service.application.services.dedup import StoredNewsFilter


@dataclass
class Item:
    url: str


class FakeStoredNewsIndex:
    def __init__(self, *stored: str) -> None:
        self.stored = set(stored)
        self.queried: list[str] = []

    async def list_stored_urls(self, urls: list[str]) -> set[str]:
        self.queried = urls
        return self.stored.intersection(urls)


@pytest.mark.asyncio
async def test_drops_only_the_stored_items():
    index = FakeStoredNewsIndex("https://example.test/a")
    items = [Item("https://example.test/a"), Item("https://example.test/b")]

    fresh = await StoredNewsFilter(index, "rss").unstored("https://example.test", items)

    assert [item.url for item in fresh] == ["https://example.test/b"]


@pytest.mark.asyncio
async def test_an_empty_list_is_returned_without_querying_the_index():
    index = FakeStoredNewsIndex()

    fresh = await StoredNewsFilter(index, "web").unstored("https://example.test", [])

    assert fresh == []
    assert index.queried == []
