"""Failure raised when summary embedding cannot complete."""


class SummaryEmbeddingError(RuntimeError):
    """The embedding provider could not encode the batch, or returned unusable vectors."""
