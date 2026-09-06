"""Current DB-backed state of one tracked legislative act."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base
from common.entities.npa import NpaTrackingStatus
from common.schemas.types import NPA_TRACKING_STATUS

URL_MAX_LENGTH = 2048
TITLE_MAX_LENGTH = 512
STAGE_MAX_LENGTH = 256
STAGE_CODE_MAX_LENGTH = 32
BILL_NUMBER_MAX_LENGTH = 64

# `sqlalchemy.text` is aliased because the model has a column named `text`.
_GEN_UUID = sql_text("gen_random_uuid()")


class Npa(Base):
    __tablename__ = "npa"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=_GEN_UUID
    )
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), unique=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    plain_title: Mapped[str | None] = mapped_column(String(90), nullable=True)
    text: Mapped[str] = mapped_column(Text, default="", server_default="")
    bill_number: Mapped[str | None] = mapped_column(String(BILL_NUMBER_MAX_LENGTH), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(STAGE_MAX_LENGTH), nullable=True)
    stage_code: Mapped[str | None] = mapped_column(String(STAGE_CODE_MAX_LENGTH), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_status: Mapped[NpaTrackingStatus] = mapped_column(
        NPA_TRACKING_STATUS,
        default=NpaTrackingStatus.UNSUPPORTED,
        server_default=NpaTrackingStatus.UNSUPPORTED.value,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    initial_summary_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    article_changes: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
