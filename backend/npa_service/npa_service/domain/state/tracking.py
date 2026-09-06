"""Active tracking state: checks continue until official publication."""

from common.entities.npa import NpaTrackingStatus

from npa_service.domain.state.tracking_state import TrackingState


class Tracking(TrackingState):
    @property
    def status(self) -> NpaTrackingStatus:
        return NpaTrackingStatus.TRACKING

    @property
    def can_check(self) -> bool:
        return True

    def transition(self, is_published: bool) -> TrackingState:
        if not is_published:
            return self

        from npa_service.domain.state.published import Published

        return Published()
