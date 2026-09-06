"""Failure raised when local summary embedding cannot complete."""


class SummaryEmbeddingError(RuntimeError):
    """The local summary embedding model could not encode the batch."""
