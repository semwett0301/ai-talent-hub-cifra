"""Source — DB-backed schema (SQLAlchemy ORM), owned by source_service."""

from datetime import datetime

from common.core.base import Base
from common.enums import SourceType
from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

_SOURCE_TYPE = Enum(
    SourceType,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    native_enum=False,
    length=16,
    name="source_type",
)


class Source(Base):
    __tablename__ = "source"

    type: Mapped[SourceType] = mapped_column(_SOURCE_TYPE)
    name: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(1024), primary_key=True)
    # How often to poll a pull source (RSS/Web), seconds. Null for push (Telegram).
    poll_interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
