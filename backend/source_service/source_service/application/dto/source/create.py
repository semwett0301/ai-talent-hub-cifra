"""Input DTO for creating a Source. Neither `type` nor `poll_interval_seconds` is
accepted — SourceService derives both from the detected type."""

from common.entities.source import SourceReliability
from pydantic import BaseModel

from .link import SourceLink


class SourceCreate(BaseModel):
    name: str
    link: SourceLink
    is_enabled: bool = True
    reliability: SourceReliability = SourceReliability.MEDIUM
