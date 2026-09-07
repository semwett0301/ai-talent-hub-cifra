"""StoredNewsRepo — StoredNewsIndex over the shared `news` table, a fresh session per call."""

from common.core.db import async_session_factory
from common.core.logging import get_logger
from common.schemas import News
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from source_service.application.ports.source import StoredNewsIndex

LOOKUP_ERRORS = (SQLAlchemyError, OSError)

logger = get_logger(__name__)


class StoredNewsRepo(StoredNewsIndex):
    """Read-only: `news` belongs to `news_service`, this only asks what is already there."""

    async def list_stored_urls(self, urls: list[str]) -> set[str]:
        if not urls:
            return set()

        statement = select(News.url).where(News.url.in_(urls))
        try:
            async with async_session_factory() as session:
                stored = (await session.execute(statement)).scalars().all()
        except LOOKUP_ERRORS as error:
            logger.warning("stored news lookup failed: urls=%d (%s)", len(urls), error)
            return set()

        return set(stored)
