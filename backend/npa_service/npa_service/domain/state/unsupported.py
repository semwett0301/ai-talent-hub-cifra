"""Terminal state for rows created before State Duma tracking was introduced."""

from common.entities.npa import NpaTrackingStatus

from npa_service.domain.state.tracking_state import TrackingState


class Unsupported(TrackingState):
    @property
    def status(self) -> NpaTrackingStatus:
        return NpaTrackingStatus.UNSUPPORTED

    @property
    def can_check(self) -> bool:
        return False

    def transition(self, is_published: bool) -> TrackingState:
        return self
