"""SqlNewsTransaction — NewsTransaction over one SQLAlchemy `AsyncSession`."""

import uuid
from types import TracebackType
from typing import Self

from domain.schemas import News
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.ports import NewsTransaction


class SqlNewsTransaction(NewsTransaction):
    """Owns the session for the duration of the `async with` block.

    Changes are flushed but not committed until `commit()`; on exit anything still
    pending is rolled back and the session closed — so an exception between a staged
    write and `commit()` leaves the DB untouched.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # A no-op after a successful commit; the rollback for every other exit path.
        await self.__session.rollback()
        await self.__session.close()

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        news = await self.__session.get(News, news_id)
        if news is None:
            return None

        news.is_alert = True
        await self.__session.flush()
        return news

    async def commit(self) -> None:
        await self.__session.commit()
