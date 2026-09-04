"""Application errors — raised by use cases / repositories, mapped by the outer layers."""


class NewsStoreError(RuntimeError):
    """A batch could not be written; the caller decides whether to retry (requeue)."""
