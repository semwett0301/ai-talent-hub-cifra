"""News contract — the `news` exchange message, its source type, and its routing.

Everything the `news` domain shares between producer and consumers lives here: the
`SourceType` a post came from, the `NewsDTO` payload (flat and typed — it also carries
the source's id, name and `SourceReliability`, so a consumer never has to call back into
`source_service`), and the routing key it is published under.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from common.entities.source import SourceReliability

# Type-only: `common.schemas.Source` imports this module for `SourceType`, so a runtime
# import back would cycle. mypy resolves the cycle; the interpreter never sees it.
if TYPE_CHECKING:
    from common.schemas import Source

ROUTING_PREFIX = "news.raw"
SCHEMA_VERSION = 5


class SourceType(StrEnum):
    """How a source is collected."""

    TELEGRAM = "telegram"
    RSS = "rss"
    WEB = "web"


class NewsDTO(BaseModel):
    """A single collected news item as published to the `news` exchange.

    One flat record: what the source says about itself (denormalized, so the row outlives
    a renamed source) plus what the collector read. Optional fields stay `None` when the
    source type has nothing to offer (a Telegram post has no excerpt).
    """

    schema_version: int = SCHEMA_VERSION

    source_id: uuid.UUID
    source_link: str
    source_name: str
    source_type: SourceType
    source_reliability: SourceReliability
    # Rubric / feed categories / hashtags, as the source labelled the item.
    source_tags: list[str] = Field(default_factory=list)

    url: str
    title: str
    text: str
    excerpt: str | None = None
    published_at: datetime | None = None
    # When the source itself last edited the item (page `modified`, post `edit_date`).
    updated_at: datetime | None = None

    @classmethod
    def for_source(
        cls,
        source: "Source",
        *,
        url: str,
        title: str,
        text: str,
        excerpt: str | None = None,
        published_at: datetime | None = None,
        updated_at: datetime | None = None,
        source_tags: list[str] | None = None,
    ) -> "NewsDTO":
        """Build from a source's identity plus what a collector read from it."""
        return cls(
            source_id=source.id,
            source_link=source.link,
            source_name=source.name,
            source_type=source.type,
            source_reliability=source.reliability,
            source_tags=source_tags or [],
            url=url,
            title=title,
            text=text,
            excerpt=excerpt,
            published_at=published_at,
            updated_at=updated_at,
        )


def routing_key(source_type: SourceType) -> str:
    """`news.raw.telegram` / `news.raw.rss` / `news.raw.web`."""
    return f"{ROUTING_PREFIX}.{source_type.value}"
