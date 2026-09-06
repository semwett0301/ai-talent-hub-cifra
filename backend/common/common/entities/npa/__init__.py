"""NPA contract — the legislative-act shape shared by news_service and npa_service."""

from common.entities.npa.dto import NpaDTO
from common.entities.npa.status import NpaTrackingStatus

__all__ = ["NpaDTO", "NpaTrackingStatus"]
