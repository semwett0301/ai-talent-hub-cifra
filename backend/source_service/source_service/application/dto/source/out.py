"""Output DTO for a Source (ORM is never exposed directly)."""

from datetime import datetime

from common.enums import SourceType
from pydantic import BaseModel, ConfigDict


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: SourceType
    name: str
    link: str
    poll_interval_seconds: int | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
