"""Output DTO for a Source (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from domain.entities.news import SourceType
from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: SourceType
    name: str
    link: str
    poll_interval_seconds: int | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
