"""Column types shared by several ORM models (enum-backed VARCHARs)."""

from sqlalchemy import Enum

from domain.entities.news import SourceType
from domain.entities.source import SourceReliability

SOURCE_TYPE = Enum(
    SourceType,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    native_enum=False,
    length=16,
    name="source_type",
)

SOURCE_RELIABILITY = Enum(
    SourceReliability,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    native_enum=False,
    length=8,
    name="source_reliability",
)
