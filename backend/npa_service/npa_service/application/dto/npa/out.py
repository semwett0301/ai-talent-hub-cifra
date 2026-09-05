"""Output DTO for an Npa row (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NpaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    title: str
    text: str
    published_at: datetime | None
    created_at: datetime
