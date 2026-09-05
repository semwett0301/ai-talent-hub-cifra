"""Shared domain errors — failure signals any service or infra mechanism may raise or catch."""

from common.core.errors.batch_store import BatchStoreError

__all__ = ["BatchStoreError"]
