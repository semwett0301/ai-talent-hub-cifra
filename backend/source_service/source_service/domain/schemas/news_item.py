"""NewsItem — in-memory schema: the normalized unit every collector emits."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class NewsItem:
    url: str
    text: str
    published_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)
