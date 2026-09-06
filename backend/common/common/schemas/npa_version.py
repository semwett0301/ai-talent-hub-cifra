"""Immutable snapshot of one observed State Duma bill version."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base
from common.schemas.npa import STAGE_CODE_MAX_LENGTH, STAGE_MAX_LENGTH, URL_MAX_LENGTH

_GEN_UUID = sql_text("gen_random_uuid()")


class NpaVersion(Base):
    __tablename__ = "npa_version"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=_GEN_UUID
    )
    npa_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("npa.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(STAGE_MAX_LENGTH))
    stage_code: Mapped[str] = mapped_column(String(STAGE_CODE_MAX_LENGTH))
    text: Mapped[str] = mapped_column(Text)
    document_url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH))
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    article_changes: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
