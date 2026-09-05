"""Scheduler port — periodic pull jobs, one per source, without naming a library.

`SourceRegistry` decides *that* an enabled pull source runs every N seconds; how that
recurrence is implemented (APScheduler today) stays behind this port.
"""

import uuid
from typing import Protocol


class PullRun(Protocol):
    """One source's periodic work — collect and publish, handed to the scheduler."""

    async def __call__(self, source_id: uuid.UUID) -> None: ...


class JobScheduler(Protocol):
    """Recurring jobs addressed by source id. Both methods are idempotent: scheduling an
    already-scheduled source replaces it, unscheduling an unknown one does nothing."""

    def schedule(self, source_id: uuid.UUID, seconds: int, run: PullRun) -> None: ...

    def unschedule(self, source_id: uuid.UUID) -> None: ...
