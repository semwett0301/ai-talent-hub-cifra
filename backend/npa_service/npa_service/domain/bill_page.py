"""Metadata parsed from one State Duma bill page."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BillPage:
    url: str
    bill_number: str
    title: str
    stage: str
    stage_code: str
    document_url: str
    updated_at: datetime
    published_at: datetime | None
