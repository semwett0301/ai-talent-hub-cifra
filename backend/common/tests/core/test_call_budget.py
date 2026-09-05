"""`LlmCallBudget`: the total cap, the concurrency gate, and the unlimited setting."""

import asyncio

from common.core.llm import LlmCallBudget


class _Counter:
    """Counts the calls and the peak number of them running at the same time."""

    def __init__(self) -> None:
        self.calls = 0
        self.max_active = 0
        self.__active = 0

    async def run(self) -> int:
        self.calls += 1
        self.__active += 1
        self.max_active = max(self.max_active, self.__active)
        await asyncio.sleep(0)
        self.__active -= 1
        return self.calls


async def _drain(budget: LlmCallBudget, counter: _Counter, times: int) -> list[int | None]:
    return list(await asyncio.gather(*(budget.run(counter.run) for _ in range(times))))


async def test_stops_calling_past_the_total_cap() -> None:
    budget, counter = LlmCallBudget(max_calls=3, concurrency=5), _Counter()

    answers = await _drain(budget, counter, 10)

    assert counter.calls == 3
    assert budget.used == 3
    assert sum(1 for answer in answers if answer is None) == 7


async def test_never_runs_more_than_concurrency_at_once() -> None:
    budget, counter = LlmCallBudget(max_calls=20, concurrency=2), _Counter()

    await _drain(budget, counter, 20)

    assert counter.calls == 20
    assert counter.max_active <= 2


async def test_zero_max_calls_means_unlimited() -> None:
    budget, counter = LlmCallBudget(max_calls=0, concurrency=4), _Counter()

    await _drain(budget, counter, 12)

    assert counter.calls == 12
    assert budget.is_exhausted is False
