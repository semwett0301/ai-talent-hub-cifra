"""Input DTO for partially updating a Source."""

from pydantic import BaseModel


class SourceUpdate(BaseModel):
    name: str | None = None
    link: str | None = None
    poll_interval_seconds: int | None = None
    is_enabled: bool | None = None
