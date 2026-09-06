"""NPA contract — the shape of a legislative act (нормативно-правовой акт) as it crosses
service boundaries.

`news_service` posts it when a reader escalates an alert. The NPA service treats only
its `url` as input and reloads authoritative metadata/text from the State Duma card.
"""

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class NpaDTO(BaseModel):
    """A cross-service NPA candidate; the destination verifies its URL and contents."""

    url: HttpUrl
    title: str
    text: str = ""
    published_at: datetime | None = None
