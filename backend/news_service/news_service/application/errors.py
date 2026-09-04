"""Application errors — raised by use cases / repositories, mapped by the outer layers."""

from domain.core.rabbit import BatchStoreError


class NewsStoreError(BatchStoreError):
    """A news batch could not be written; the shared consumer requeues it."""
