"""Complete observable state of a State Duma bill at one point in time."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BillSnapshot:
    url: str
    bill_number: str
    title: str
    stage: str
    stage_code: str
    text: str
    document_url: str
    updated_at: datetime
    published_at: datetime | None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None
