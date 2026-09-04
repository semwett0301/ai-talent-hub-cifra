"""SourceRepo — SourceRepository over SQLAlchemy, a fresh session per call."""

from common.core.session import async_session_factory
from common.enums import SourceType
from sqlalchemy import select

from source_service.application.ports import SourceRepository
from source_service.domain.schemas import Source


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

    async def get(self, link: str) -> Source | None:
        async with async_session_factory() as session:
            return await session.get(Source, link)

    async def create(self, data: dict) -> Source:
        async with async_session_factory() as session:
            source = Source(**data)
            session.add(source)
            await session.commit()
            await session.refresh(source)
            return source

    async def update(self, source: Source, data: dict) -> Source:
        async with async_session_factory() as session:
            merged = await session.merge(source)
            for key, value in data.items():
                setattr(merged, key, value)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, source: Source) -> None:
        async with async_session_factory() as session:
            await session.delete(await session.merge(source))
            await session.commit()
