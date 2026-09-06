"""State-pattern contract for the NPA tracking lifecycle."""

from typing import Protocol

from common.entities.npa import NpaTrackingStatus


class TrackingState(Protocol):
    @property
    def status(self) -> NpaTrackingStatus: ...

    @property
    def can_check(self) -> bool: ...

    def transition(self, is_published: bool) -> "TrackingState": ...
