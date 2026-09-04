"""BatchStoreError — the one signal a handler raises to have a batch requeued."""


class BatchStoreError(RuntimeError):
    """The batch could not be persisted; the consumer nacks it back to the broker.

    Service-specific store errors subclass this so the shared consumer can catch them
    without knowing the service."""
