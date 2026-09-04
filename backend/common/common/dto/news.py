"""News DTO — the RabbitMQ message contract shared across services."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from common.enums import SourceType


class NewsDTO(BaseModel):
    """A single collected news item as published to the `news` exchange."""

    schema_version: int = 3
    source_id: uuid.UUID
    source_type: SourceType
    url: str
    text: str
    published_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
