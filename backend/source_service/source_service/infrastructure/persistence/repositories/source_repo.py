"""SourceRepo — implements the SourceRepository port over SQLAlchemy."""

from __future__ import annotations

from common.enums import SourceType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from source_service.infrastructure.persistence.schemas import Source


class SourceRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Source]:
        result = await self.session.execute(select(Source).order_by(Source.id))
        return list(result.scalars().all())

    async def list_enabled(self, type: SourceType | None = None) -> list[Source]:
        stmt = select(Source).where(Source.is_enabled.is_(True))
        if type is not None:
            stmt = stmt.where(Source.type == type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, source_id: int) -> Source | None:
        return await self.session.get(Source, source_id)

    async def create(self, data: dict) -> Source:
        source = Source(**data)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def update(self, source: Source, data: dict) -> Source:
        for key, value in data.items():
            setattr(source, key, value)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def delete(self, source: Source) -> None:
        await self.session.delete(source)
        await self.session.commit()
