"""`LlmDateBudget` — a hard per-crawl cap on LLM date calls, plus a concurrency gate."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

AnswerT = TypeVar("AnswerT")


class LlmDateBudget:
    """One per site crawl: `remaining` calls in total, at most `concurrency` in flight.
    `run` returns `(answer, was_called)`; past the budget it returns `(None, False)`."""

    def __init__(self, *, max_calls: int, concurrency: int) -> None:
        self.remaining = max(0, max_calls)
        self.used = 0
        self.max_active = 0
        self.__active = 0
        self.__lock = asyncio.Lock()
        self.__semaphore = asyncio.Semaphore(max(1, concurrency))

    async def run(
        self, action: Callable[[], Awaitable[AnswerT | None]]
    ) -> tuple[AnswerT | None, bool]:
        async with self.__lock:
            if self.remaining <= 0:
                return None, False
            self.remaining -= 1
            self.used += 1

        async with self.__semaphore:
            self.__active += 1
            self.max_active = max(self.max_active, self.__active)
            try:
                return await action(), True
            finally:
                self.__active -= 1
