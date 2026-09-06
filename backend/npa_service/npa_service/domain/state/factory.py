"""Build the behavior object for a persisted tracking status."""

from common.entities.npa import NpaTrackingStatus

from npa_service.domain.state.published import Published
from npa_service.domain.state.tracking import Tracking
from npa_service.domain.state.tracking_state import TrackingState
from npa_service.domain.state.unsupported import Unsupported


def build_tracking_state(status: NpaTrackingStatus) -> TrackingState:
    states: dict[NpaTrackingStatus, TrackingState] = {
        NpaTrackingStatus.TRACKING: Tracking(),
        NpaTrackingStatus.PUBLISHED: Published(),
        NpaTrackingStatus.UNSUPPORTED: Unsupported(),
    }
    return states[status]
