"""Output DTO for a Source (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from common.entities.news import SourceType
from common.entities.source import SourceReliability
from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: SourceType
    name: str
    link: str
    poll_interval_seconds: int | None
    is_enabled: bool
    reliability: SourceReliability
    created_at: datetime
    updated_at: datetime
