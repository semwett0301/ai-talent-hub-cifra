"""SourceRepo — SourceRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.entities.news import SourceType
from common.schemas import Source
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from source_service.application.errors import SourceAlreadyExistsError
from source_service.application.ports.source import SourceRepository


async def _commit(session: AsyncSession, link: str) -> None:
    """`normalized_link` is unique, so a repeated address surfaces here."""
    try:
        await session.commit()
    except IntegrityError as error:
        raise SourceAlreadyExistsError(link) from error


class SourceRepo(SourceRepository):
    """Each call runs in its own session (unit of work).

    No shared session state, so the same repo serves request handlers and the
    long-lived background aggregators that run jobs concurrently. A `source`
    handed to update/delete is merged into the fresh session first.
    """

    async def list_all(self) -> list[Source]:
        async with async_session_factory() as session:
            result = await session.execute(select(Source).order_by(Source.link))
            return list(result.scalars().all())

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]:
        stmt = select(Source).where(Source.is_enabled.is_(True))
        if type is not None:
            stmt = stmt.where(Source.type == type)
        async with async_session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get(self, source_id: uuid.UUID) -> Source | None:
        async with async_session_factory() as session:
            return await session.get(Source, source_id)

    async def create(self, data: dict) -> Source:
        async with async_session_factory() as session:
            source = Source(**data)
            session.add(source)

            await _commit(session, source.link)
            await session.refresh(source)
            return source

    async def update(self, source: Source, data: dict) -> Source:
        async with async_session_factory() as session:
            merged = await session.merge(source)
            for key, value in data.items():
                setattr(merged, key, value)

            await _commit(session, merged.link)
            await session.refresh(merged)
            return merged

    async def delete(self, source: Source) -> None:
        async with async_session_factory() as session:
            await session.delete(await session.merge(source))
            await session.commit()
