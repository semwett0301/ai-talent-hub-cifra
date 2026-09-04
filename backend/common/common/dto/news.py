"""News DTO — the RabbitMQ message contract shared across services."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from common.enums import SourceType


class NewsDTO(BaseModel):
    """A single collected news item as published to the `news` exchange."""

    schema_version: int = 2
    source_link: str
    source_type: SourceType
    url: str
    text: str
    published_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
