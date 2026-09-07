"""Normalized local CPU embeddings for pgvector candidate retrieval."""

from common.core.logging import get_logger
from common.schemas.news_event_state import SUMMARY_EMBEDDING_DIMENSION
from sentence_transformers import SentenceTransformer

from news_service.application.errors import SummaryEmbeddingError
from news_service.application.ports import SummaryEmbedder

logger = get_logger(__name__)


class SentenceTransformerSummaryEmbedder(SummaryEmbedder):
    def __init__(self, model_name: str, batch_size: int) -> None:
        self.__model_name = model_name
        self.__batch_size = batch_size
        self.__model: SentenceTransformer | None = None

    def embed(self, summaries: list[str]) -> list[list[float]]:
        if not summaries:
            return []
        logger.info(
            "summary embedding started: items=%d model=%s", len(summaries), self.__model_name
        )
        try:
            vectors = self.__get_model().encode(
                summaries,
                batch_size=self.__batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise SummaryEmbeddingError(
                f"summary embedding failed: model={self.__model_name} items={len(summaries)}"
            ) from error

        values = vectors.tolist()
        if any(len(vector) != SUMMARY_EMBEDDING_DIMENSION for vector in values):
            raise SummaryEmbeddingError(
                f"unexpected embedding dimension: expected={SUMMARY_EMBEDDING_DIMENSION}"
            )
        logger.info(
            "summary embedding completed: items=%d model=%s", len(values), self.__model_name
        )
        return values

    def __get_model(self) -> SentenceTransformer:
        if self.__model is None:
            self.__model = SentenceTransformer(self.__model_name, device="cpu")
        return self.__model
