"""Input DTO for creating a Source. `type` is not accepted — SourceService detects it."""

from common.entities.source import SourceReliability
from pydantic import BaseModel

from .link import SourceLink


class SourceCreate(BaseModel):
    name: str
    link: SourceLink
    poll_interval_seconds: int | None = None
    is_enabled: bool = True
    reliability: SourceReliability = SourceReliability.MEDIUM
