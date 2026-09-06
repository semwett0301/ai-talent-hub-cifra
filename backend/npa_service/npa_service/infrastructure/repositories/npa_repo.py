"""SQLAlchemy persistence for current NPA state and immutable versions."""

import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from common.core.db import async_session_factory
from common.entities.npa import NpaTrackingStatus
from common.schemas import Npa, NpaVersion
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from npa_service.application.errors import NpaAlreadyExistsError
from npa_service.application.ports import NpaRepository
from npa_service.domain import BillSnapshot, ChangeSummary, TrackedUpdate


def _snapshot_fields(snapshot: BillSnapshot) -> dict[str, Any]:
    return {
        "url": snapshot.url,
        "bill_number": snapshot.bill_number,
        "title": snapshot.title,
        "stage": snapshot.stage,
        "stage_code": snapshot.stage_code,
        "text": snapshot.text,
        "document_url": snapshot.document_url,
        "source_updated_at": snapshot.updated_at,
        "last_checked_at": datetime.now(UTC),
        "published_at": snapshot.published_at,
        "summary": None,
        "summary_kind": None,
        "initial_summary_status": "pending",
        "article_changes": [],
    }


def _version_fields(
    npa_id: uuid.UUID, snapshot: BillSnapshot, change: ChangeSummary | None
) -> dict[str, Any]:
    return {
        "npa_id": npa_id,
        "stage": snapshot.stage,
        "stage_code": snapshot.stage_code,
        "text": snapshot.text,
        "document_url": snapshot.document_url,
        "source_updated_at": snapshot.updated_at,
        "summary": change.overall if change else None,
        "summary_kind": "change" if change else None,
        "article_changes": [asdict(article) for article in change.articles] if change else [],
    }


def _apply_fields(row: Npa, update_value: TrackedUpdate) -> None:
    fields = _snapshot_fields(update_value.snapshot)
    fields.pop("initial_summary_status")
    fields["tracking_status"] = update_value.status
    fields["summary"] = update_value.change.overall if update_value.change else None
    fields["summary_kind"] = "change" if update_value.change else None
    fields["article_changes"] = (
        [asdict(article) for article in update_value.change.articles] if update_value.change else []
    )
    for name, value in fields.items():
        setattr(row, name, value)


class NpaRepo(NpaRepository):
    async def list_all(self, limit: int, offset: int) -> list[Npa]:
        stmt = select(Npa).order_by(Npa.created_at.desc(), Npa.id).limit(limit).offset(offset)
        async with async_session_factory() as session:
            rows = await session.execute(stmt)
            return list(rows.scalars().all())

    async def get(self, npa_id: uuid.UUID) -> Npa | None:
        async with async_session_factory() as session:
            return await session.get(Npa, npa_id)

    async def list_tracking(self) -> list[Npa]:
        stmt = select(Npa).where(Npa.tracking_status == NpaTrackingStatus.TRACKING)
        async with async_session_factory() as session:
            rows = await session.execute(stmt)
            return list(rows.scalars().all())

    async def list_versions(self, npa_id: uuid.UUID) -> list[NpaVersion]:
        stmt = (
            select(NpaVersion)
            .where(NpaVersion.npa_id == npa_id)
            .order_by(NpaVersion.source_updated_at.desc(), NpaVersion.id)
        )
        async with async_session_factory() as session:
            rows = await session.execute(stmt)
            return list(rows.scalars().all())

    async def add(self, snapshot: BillSnapshot, status: NpaTrackingStatus) -> Npa:
        row = Npa(**_snapshot_fields(snapshot), tracking_status=status)
        async with async_session_factory() as session:
            session.add(row)
            try:
                await session.flush()
                session.add(NpaVersion(**_version_fields(row.id, snapshot, None)))
                await session.commit()
            except IntegrityError as error:
                raise NpaAlreadyExistsError(row.url) from error
            await session.refresh(row)
            return row

    async def set_initial_summary(self, npa_id: uuid.UUID, summary: str) -> None:
        async with async_session_factory() as session:
            row = await session.get(Npa, npa_id)
            if row is None:
                return
            first_version = await session.scalar(
                select(NpaVersion)
                .where(NpaVersion.npa_id == npa_id)
                .order_by(NpaVersion.created_at, NpaVersion.id)
                .limit(1)
            )
            if first_version is not None:
                first_version.summary = summary
                first_version.summary_kind = "initial"
            if row.summary_kind is None:
                row.summary = summary
                row.summary_kind = "initial"
            row.initial_summary_status = "ready"
            await session.commit()

    async def mark_initial_summary_failed(self, npa_id: uuid.UUID) -> None:
        stmt = update(Npa).where(Npa.id == npa_id).values(initial_summary_status="failed")
        async with async_session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def apply_update(self, npa_id: uuid.UUID, update_value: TrackedUpdate) -> Npa:
        async with async_session_factory() as session:
            row = await session.get(Npa, npa_id)
            if row is None:
                raise LookupError(f"npa not found: id={npa_id}")
            _apply_fields(row, update_value)
            version_fields = _version_fields(npa_id, update_value.snapshot, update_value.change)
            session.add(NpaVersion(**version_fields))
            await session.commit()
            await session.refresh(row)
            return row

    async def mark_checked(
        self, npa_id: uuid.UUID, snapshot: BillSnapshot, checked_at: datetime
    ) -> None:
        stmt = (
            update(Npa)
            .where(Npa.id == npa_id)
            .values(
                title=snapshot.title,
                source_updated_at=snapshot.updated_at,
                last_checked_at=checked_at,
            )
        )
        async with async_session_factory() as session:
            await session.execute(stmt)
            await session.commit()
