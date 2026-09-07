"""Batch failure raised when news persistence cannot complete."""

from common.core.errors import BatchStoreError


class NewsStoreError(BatchStoreError):
    """A news batch could not be written; the shared consumer retries it by policy."""
