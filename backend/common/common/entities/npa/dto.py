"""NPA contract — the shape of a legislative act (нормативно-правовой акт) as it crosses
service boundaries.

`news_service` posts it to `npa_service` when a reader escalates a news alert into an
act; `npa_service` accepts the same shape on its create endpoint. `url` is the act's
identity — unique per stored row.
"""

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class NpaDTO(BaseModel):
    """A legislative act to register. `url` identifies it (unique in the store)."""

    url: HttpUrl
    title: str
    text: str = ""
    published_at: datetime | None = None
