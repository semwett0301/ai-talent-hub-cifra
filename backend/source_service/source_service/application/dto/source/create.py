"""Input DTO for creating a Source. `type` is not accepted — SourceService detects it."""

from domain.entities.source import SourceReliability
from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    link: str
    poll_interval_seconds: int | None = None
    is_enabled: bool = True
    reliability: SourceReliability = SourceReliability.MEDIUM
