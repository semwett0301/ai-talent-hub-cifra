"""BatchStoreError — a batch of items could not be persisted."""


class BatchStoreError(RuntimeError):
    """Raised by whatever persists a batch when the write as a whole failed.

    Transport-agnostic: the mechanism that fed the batch (a bus consumer, a scheduled
    loader, …) catches it and decides what happens to the items — retry, requeue, drop.
    Service-specific store errors subclass it so shared code can catch them without
    knowing the service."""
