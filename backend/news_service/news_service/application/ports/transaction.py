"""NewsTransaction port — one DB transaction over news, held open across other work."""

import uuid
from types import TracebackType
from typing import Protocol, Self

from common.schemas import News


class NewsTransaction(Protocol):
    """A unit of work opened by `NewsRepository.begin()`.

    Mutations are *staged* until `commit()`; leaving the `async with` block without a
    commit — or by exception — rolls them back. This is what lets a use case make a DB
    change conditional on an external call succeeding.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        """Stage `is_alert = true` on one row; returns it, or None when the id is unknown."""
        ...

    async def commit(self) -> None:
        """Persist everything staged so far."""
        ...
