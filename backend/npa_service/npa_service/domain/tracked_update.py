"""A snapshot and its optional explanation ready for persistence."""

from dataclasses import dataclass

from common.entities.npa import NpaTrackingStatus

from npa_service.domain.bill_snapshot import BillSnapshot
from npa_service.domain.change_summary import ChangeSummary


@dataclass(frozen=True, slots=True)
class TrackedUpdate:
    snapshot: BillSnapshot
    status: NpaTrackingStatus
    change: ChangeSummary | None = None
