"""Input DTO for creating a Source."""

from common.enums import SourceType
from pydantic import BaseModel


class SourceCreate(BaseModel):
    type: SourceType
    name: str
    link: str
    poll_interval_seconds: int | None = None
    is_enabled: bool = True
