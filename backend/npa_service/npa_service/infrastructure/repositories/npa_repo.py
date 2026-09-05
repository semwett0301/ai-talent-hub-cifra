"""NpaRepo — NpaRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.entities.npa import NpaDTO
from common.schemas import Npa
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from npa_service.application.errors import NpaAlreadyExistsError
from npa_service.application.ports import NpaRepository


class NpaRepo(NpaRepository):
    """Each call runs in its own session (unit of work); no shared session state."""

    async def list_all(self, limit: int, offset: int) -> list[Npa]:
        stmt = select(Npa).order_by(Npa.created_at.desc(), Npa.id).limit(limit).offset(offset)
        async with async_session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get(self, npa_id: uuid.UUID) -> Npa | None:
        async with async_session_factory() as session:
            return await session.get(Npa, npa_id)

    async def add(self, act: NpaDTO) -> Npa:
        # `url` is an HttpUrl on the contract; the column holds its string form.
        row = Npa(**act.model_dump() | {"url": str(act.url)})

        async with async_session_factory() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as error:
                raise NpaAlreadyExistsError(row.url) from error

            await session.refresh(row)
            return row
