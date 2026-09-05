"""Npa — DB-backed schema (SQLAlchemy ORM), owned by npa_service.

Mirrors `common.entities.npa.NpaDTO` plus a DB-generated `id` and `created_at`. `url`
is unique — one row per act.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base

URL_MAX_LENGTH = 2048
TITLE_MAX_LENGTH = 512

# `sqlalchemy.text` is aliased because the model has a column named `text`.
_GEN_UUID = sql_text("gen_random_uuid()")


class Npa(Base):
    __tablename__ = "npa"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=_GEN_UUID
    )
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), unique=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    text: Mapped[str] = mapped_column(Text, default="", server_default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
