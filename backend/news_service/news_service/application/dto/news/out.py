"""Output DTO for a News item (ORM is never exposed directly).

Deliberately unchanged by the flat-row rework except for `raw`, which the row no longer
has; the new columns (`title`, `excerpt`, …) are exposed when the news API is reworked.
"""

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
    source_type: SourceType
    source_reliability: SourceReliability
    url: str
    text: str
    published_at: datetime | None
    is_alert: bool
    created_at: datetime
