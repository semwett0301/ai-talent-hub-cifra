"""SourceRepo — SourceRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.entities.news import SourceType
from common.schemas import RssLink, Source
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from source_service.application.errors import SourceAlreadyExistsError
from source_service.application.ports.source import SourceRepository


async def _save(session: AsyncSession, source: Source, feed_urls: list[str] | None) -> None:
    """The source and (when given) its feed list under one commit. `normalized_link` is
    unique, so a repeated address surfaces here — at the flush or at the commit."""
    try:
        if feed_urls is not None:
            await _replace_feed_links(session, source, feed_urls)
        await session.commit()
    except IntegrityError as error:
        raise SourceAlreadyExistsError(source.link) from error


async def _replace_feed_links(session: AsyncSession, source: Source, feed_urls: list[str]) -> None:
    """The old feed rows go and the new ones come in the same transaction as the source
    itself; the source is flushed first so the `rss_link` trigger sees its current type."""
    await session.flush()
    await session.execute(delete(RssLink).where(RssLink.source_id == source.id))

    session.add_all(RssLink(source_id=source.id, url=url) for url in feed_urls)


class SourceRepo(SourceRepository):
    """Each call runs in its own session (unit of work).

    No shared session state, so the same repo serves request handlers and the
    long-lived background aggregators that run jobs concurrently. A `source`
    handed to update/delete is merged into the fresh session first. A source and its
    feed URLs are two inserts under one `COMMIT` — never a source without its feeds.
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

    async def create(self, data: dict, feed_urls: list[str]) -> Source:
        async with async_session_factory() as session:
            source = Source(**data)
            session.add(source)

            await _save(session, source, feed_urls)
            await session.refresh(source)
            return source

    async def update(
        self, source: Source, data: dict, feed_urls: list[str] | None = None
    ) -> Source:
        async with async_session_factory() as session:
            merged = await session.merge(source)
            for key, value in data.items():
                setattr(merged, key, value)

            await _save(session, merged, feed_urls)
            await session.refresh(merged)
            return merged

    async def delete(self, source: Source) -> None:
        async with async_session_factory() as session:
            await session.delete(await session.merge(source))
            await session.commit()
