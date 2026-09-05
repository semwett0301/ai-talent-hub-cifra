"""`LlmCallBudget` — how many LLM calls one run may make, and how many at once."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

AnswerT = TypeVar("AnswerT")

UNLIMITED = 0


class LlmCallBudget:
    """One per run (a site crawl, a batch, a job): at most `max_calls` calls in total
    (`0` = unlimited) and at most `concurrency` of them in flight. Past the cap `run`
    answers `None` without touching the model."""

    def __init__(self, *, max_calls: int, concurrency: int) -> None:
        self.__max_calls = max(UNLIMITED, max_calls)
        self.__lock = asyncio.Lock()
        self.__gate = asyncio.Semaphore(max(1, concurrency))
        self.used = 0

    @property
    def is_exhausted(self) -> bool:
        return self.__max_calls != UNLIMITED and self.used >= self.__max_calls

    async def run(self, action: Callable[[], Awaitable[AnswerT | None]]) -> AnswerT | None:
        """The action's answer, or `None` when the budget is spent (the action never runs)
        or the action itself answered nothing."""
        if not await self.__reserve():
            return None

        async with self.__gate:
            return await action()

    async def __reserve(self) -> bool:
        """One call off the total, under a lock — concurrent callers never overshoot."""
        async with self.__lock:
            if self.is_exhausted:
                return False
            self.used += 1
            return True
