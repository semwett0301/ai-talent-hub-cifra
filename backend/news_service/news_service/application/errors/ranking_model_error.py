"""Failure raised when cluster relevance inference cannot complete."""


class RankingModelError(RuntimeError):
    """Impact assessment or semantic reranking failed at the model boundary."""
