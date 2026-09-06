"""Output DTO for an Npa row (ORM is never exposed directly)."""

import uuid
from datetime import datetime

from common.entities.npa import NpaTrackingStatus
from pydantic import BaseModel, ConfigDict

from npa_service.application.dto.npa.article_change_out import ArticleChangeOut


class NpaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    bill_number: str | None
    title: str
    stage: str | None
    stage_code: str | None
    document_url: str | None
    source_updated_at: datetime | None
    last_checked_at: datetime | None
    tracking_status: NpaTrackingStatus
    summary: str | None
    article_changes: list[ArticleChangeOut]
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
