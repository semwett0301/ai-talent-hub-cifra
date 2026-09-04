import asyncio
from types import SimpleNamespace

import pytest
from source_service.application.web_crawl.extractor import (
    ArticleExtractor,
    LLMDateGate,
)
from source_service.application.web_crawl.models import (
    ArticleCandidate,
)
from source_service.application.web_crawl.settings import RuntimeSettings


class FakeClient:
    def __init__(self):
        self.calls: list[list[str]] = []

    async def crawl_articles(self, urls: list[str]):
        self.calls.append(urls)
        return [SimpleNamespace(url=url) for url in urls]


@pytest.mark.asyncio
async def test_stops_after_a_full_batch_of_reliably_old_dates():
    client = FakeClient()
    settings = RuntimeSettings(
        article_batch_size=2,
        stop_on_out_of_scope_batches=True,
        out_of_scope_consecutive_batches=1,
        out_of_scope_min_resolved_dates_per_batch=2,
    )
    extractor = ArticleExtractor(client, settings)

    async def old_date(*_args):
        return None, False, "out_of_scope"

    extractor._extract_one = old_date  # type: ignore[method-assign]
    candidates = [ArticleCandidate(url=f"https://example.test/news/{index}") for index in range(5)]

    records = await extractor.extract_many(candidates, "example")

    assert records == []
    assert client.calls == [["https://example.test/news/0", "https://example.test/news/1"]]
    assert extractor.last_run_stats["stopped_early"] is True
    assert extractor.last_run_stats["fetched_urls"] == 2


@pytest.mark.asyncio
async def test_llm_gate_applies_concurrency_and_total_budget():
    gate = LLMDateGate(max_calls=3, concurrency=2)
    active = 0
    peak = 0

    async def action():
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return "done"

    results = await asyncio.gather(*(gate.run(action) for _ in range(5)))

    assert sum(used for _, used in results) == 3
    assert gate.used == 3
    assert peak == 2
    assert gate.max_active == 2
