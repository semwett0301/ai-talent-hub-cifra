"""Input DTO for partially updating a Source. Every field is optional: the toggle sends
`is_enabled` alone, the edit form sends the rest — `exclude_unset` keeps them apart."""

from common.entities.source import SourceReliability
from pydantic import BaseModel

from .link import SourceLink


class SourceUpdate(BaseModel):
    name: str | None = None
    link: SourceLink | None = None
    poll_interval_seconds: int | None = None
    is_enabled: bool | None = None
    reliability: SourceReliability | None = None
