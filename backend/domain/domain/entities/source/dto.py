"""Source-only shapes — not part of the `news` message contract (see `entities/news`)."""

from enum import StrEnum


class SourceReliability(StrEnum):
    """How trustworthy a source's reporting is, curated per source."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
