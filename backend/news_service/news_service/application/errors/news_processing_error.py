"""Batch failure raised when a non-persistence processing stage cannot complete."""

from common.core.errors import BatchStoreError


class NewsProcessingError(BatchStoreError):
    """A summarization, embedding, or dedup stage failed; the batch must be retried."""
