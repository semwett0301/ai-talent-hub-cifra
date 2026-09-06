"""Terminal published state: the daily monitor no longer checks the bill."""

from common.entities.npa import NpaTrackingStatus

from npa_service.domain.state.tracking_state import TrackingState


class Published(TrackingState):
    @property
    def status(self) -> NpaTrackingStatus:
        return NpaTrackingStatus.PUBLISHED

    @property
    def can_check(self) -> bool:
        return False

    def transition(self, is_published: bool) -> TrackingState:
        return self
