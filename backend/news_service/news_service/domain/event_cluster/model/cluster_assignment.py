"""The durable event-cluster assignment for one news row."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClusterAssignment:
    news_id: uuid.UUID
    cluster_id: uuid.UUID
