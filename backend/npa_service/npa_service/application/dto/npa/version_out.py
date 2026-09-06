"""API representation of one persisted NPA version."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from npa_service.application.dto.npa.article_change_out import ArticleChangeOut


class NpaVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stage: str
    stage_code: str
    document_url: str
    source_updated_at: datetime
    summary: str | None
    summary_kind: str | None
    article_changes: list[ArticleChangeOut]
    created_at: datetime
