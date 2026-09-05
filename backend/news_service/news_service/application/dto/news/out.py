"""Output DTO for a News item (ORM is never exposed directly)."""

import uuid
from datetime import datetime
from typing import Any

from common.entities.news import SourceType
from common.entities.source import SourceReliability
from pydantic import BaseModel, ConfigDict


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schema_version: int
    source_id: uuid.UUID | None
    source_link: str
    source_type: SourceType
    source_reliability: SourceReliability
    url: str
    text: str
    published_at: datetime | None
    raw: dict[str, Any]
    is_alert: bool
    created_at: datetime
