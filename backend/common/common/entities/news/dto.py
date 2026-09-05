"""News contract — the `news` exchange message, its source type, and its routing.

Everything the `news` domain shares between producer and consumers lives here: the
`SourceType` a post came from, the `NewsDTO` payload (which also carries the source's
id and `SourceReliability`, so a consumer never has to call back into `source_service`),
and the routing key it is published under. Grouped by domain (news) rather than by
technical kind.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from common.entities.source import SourceReliability

ROUTING_PREFIX = "news.raw"


class SourceType(StrEnum):
    """How a source is collected."""

    TELEGRAM = "telegram"
    RSS = "rss"
    WEB = "web"


class NewsDTO(BaseModel):
    """A single collected news item as published to the `news` exchange."""

    schema_version: int = 4
    # The `source` row this came from; None once the source is gone (deleted before
    # the consumer stored the item — the consumer detaches, it never fails the batch).
    source_id: uuid.UUID | None = None
    source_link: str
    source_type: SourceType
    source_reliability: SourceReliability
    url: str
    text: str
    published_at: datetime | None = None
    # Source-specific, JSON-serializable provenance. Web crawls put the full
    # extracted article record under ``raw['article']`` so optional metadata
    # (title, canonical URL, author, image, extraction evidence) survives the
    # compact cross-service contract.
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def for_source(
        cls,
        link: str,
        source_type: SourceType,
        reliability: SourceReliability,
        *,
        source_id: uuid.UUID | None,
        url: str,
        text: str,
        published_at: datetime | None = None,
        raw: dict[str, Any] | None = None,
    ) -> "NewsDTO":
        """Build from a source's identity plus what a collector read from it.

        Takes the source's scalar fields rather than a `common.schemas.Source` row: that
        ORM model already imports this module for `SourceType`, so importing it back here
        would cycle.
        """
        return cls(
            source_id=source_id,
            source_link=link,
            source_type=source_type,
            source_reliability=reliability,
            url=url,
            text=text,
            published_at=published_at,
            raw=raw or {},
        )


def routing_key(source_type: SourceType) -> str:
    """`news.raw.telegram` / `news.raw.rss` / `news.raw.web`."""
    return f"{ROUTING_PREFIX}.{source_type.value}"
