"""A resolved publication date and how much it can be trusted."""

from datetime import datetime

from pydantic import BaseModel, Field


class PublicationDate(BaseModel, frozen=True):
    """`source` names the extraction technique that produced the date (the use case
    owns that vocabulary); `confidence` and `evidence` let a reader audit it."""

    value: datetime
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None = None
