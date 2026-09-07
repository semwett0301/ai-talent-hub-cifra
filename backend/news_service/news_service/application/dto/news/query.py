"""What the feed is asked for — search, period, hidden items. Read off the query string."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

MAX_SEARCH_LENGTH = 200


class NewsVisibility(StrEnum):
    """Which items the feed shows: the ones a reader has not hidden, only the hidden, or both."""

    VISIBLE = "visible"
    DISMISSED = "dismissed"
    ALL = "all"


class NewsQuery(BaseModel):
    # Case-insensitive substring over `title` and `text`.
    q: str | None = Field(None, min_length=1, max_length=MAX_SEARCH_LENGTH)
    # Items published (or, undated, collected) at or after this moment.
    since: datetime | None = None
    visibility: NewsVisibility = NewsVisibility.VISIBLE
    # Unset shows both; true/false narrows to escalated / not-escalated items only.
    is_alert: bool | None = None
