"""Minimal persistence state used to make batch processing idempotent."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredNewsState:
    news_id: uuid.UUID
    has_summary: bool
