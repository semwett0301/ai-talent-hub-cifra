"""One deduplicated event cluster presented to the ranking pipeline."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ClusterRankingTarget:
    cluster_id: uuid.UUID
    summaries: tuple[str, ...]
    extractions: tuple[dict[str, Any], ...]
    embeddings: tuple[tuple[float, ...], ...]
    published_at: datetime | None
    source_score: int
    member_count: int

    @property
    def document(self) -> str:
        return "\n\n".join(self.summaries)
