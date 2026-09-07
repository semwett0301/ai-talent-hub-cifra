"""`EventCluster` — a group of news items believed to describe the same real-world event.

The identity both same-event membership decisions and relevance ranking act on. This is
the bounded oldest/newest-anchor view a repository loads for one cluster.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EventCluster:
    cluster_id: uuid.UUID
    summaries: tuple[str, ...]
    primary_event_flags: tuple[bool, ...]
    published_at: datetime | None
    source_score: int
    member_count: int

    @property
    def document(self) -> str:
        return "\n\n".join(self.summaries)
