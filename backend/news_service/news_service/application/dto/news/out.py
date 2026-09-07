"""Output DTO for a News item (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from common.entities.news import SourceType
from common.entities.source import SourceReliability
from pydantic import BaseModel, ConfigDict, Field

from news_service.application.dto.news.relevance import NewsRelevanceOut


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

    # The pipeline's results, null until its stage has reached the item.
    summary: str | None
    event_cluster_id: uuid.UUID | None
    relevance: NewsRelevanceOut | None = Field(validation_alias="cluster_ranking")

    # Hidden from the feed by a reader (null = visible); escalated into a legislative act.
    dismissed_at: datetime | None
    is_alert: bool
    created_at: datetime
