"""Input DTO for partially updating a Source."""

from pydantic import BaseModel


class SourceUpdate(BaseModel):
    # link is the primary key — not updatable; recreate the source to change it.
    name: str | None = None
    poll_interval_seconds: int | None = None
    is_enabled: bool | None = None
