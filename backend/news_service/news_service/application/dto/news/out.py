"""Output DTO for a News item (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from common.entities.news import SourceType
from common.entities.source import SourceReliability
from pydantic import BaseModel, ConfigDict


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schema_version: int

    source_id: uuid.UUID
    source_link: str
    source_name: str
    source_type: SourceType
    source_reliability: SourceReliability
    source_tags: list[str]

    url: str
    title: str
    text: str
    excerpt: str | None
    published_at: datetime | None
    updated_at: datetime | None

    summary: str | None
    event_cluster_id: uuid.UUID | None

    # Hidden from the feed by a reader (null = visible); escalated into a legislative act.
    dismissed_at: datetime | None
    is_alert: bool
    created_at: datetime
