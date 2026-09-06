"""What the feed is asked for — search, period, hidden items, page. Read off the query string."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
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
    limit: int = Field(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    offset: int = Field(0, ge=0)
