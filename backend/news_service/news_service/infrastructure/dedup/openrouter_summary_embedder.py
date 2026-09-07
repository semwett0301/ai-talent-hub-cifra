"""OpenRouter Embeddings API implementation of the summary-embedder port."""

import math
from collections.abc import Iterable
from typing import Final

import httpx
from common.core.logging import get_logger
from common.core.settings import NewsDedupSettings
from common.schemas.news_event_state import SUMMARY_EMBEDDING_DIMENSION
from openrouter import OpenRouter
from openrouter.errors import NoResponseError, OpenRouterError
from openrouter.operations import CreateEmbeddingsData, CreateEmbeddingsResponse
from openrouter.utils.retries import BackoffStrategy, RetryConfig

from news_service.application.errors import SummaryEmbeddingError
from news_service.application.ports import SummaryEmbedder

EMBEDDING_ERRORS = (OpenRouterError, NoResponseError, httpx.HTTPError, TypeError, ValueError)
ENCODING_FORMAT: Final = "float"
RETRY_CONFIG = RetryConfig(
    strategy="backoff",
    backoff=BackoffStrategy(
        initial_interval=500, max_interval=8_000, exponent=2.0, max_elapsed_time=60_000
    ),
    retry_connection_errors=True,
)

logger = get_logger(__name__)


class OpenRouterSummaryEmbedder(SummaryEmbedder):
    def __init__(
        self, api_key: str | None, base_url: str | None, config: NewsDedupSettings
    ) -> None:
        if not api_key:
            raise SummaryEmbeddingError("OPENROUTER_API_KEY is required for summary embedding")
        self.__model = config.embedding_model
        self.__batch_size = config.embedding_batch_size
        self.__client = OpenRouter(api_key=api_key, server_url=base_url, retry_config=RETRY_CONFIG)

    async def embed(self, summaries: list[str]) -> list[list[float]]:
        if not summaries:
            return []
        logger.info("summary embedding started: items=%d model=%s", len(summaries), self.__model)

        vectors: list[list[float]] = []
        for batch in _chunks(summaries, self.__batch_size):
            vectors.extend(await self.__embed_batch(batch))

        logger.info("summary embedding completed: items=%d model=%s", len(vectors), self.__model)
        return vectors

    async def __embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            response = await self.__client.embeddings.generate_async(
                input=batch, model=self.__model, encoding_format=ENCODING_FORMAT
            )
        except EMBEDDING_ERRORS as error:
            raise SummaryEmbeddingError(
                f"summary embedding failed: model={self.__model} items={len(batch)}"
            ) from error

        vectors = _vectors_in_order(response, expected=len(batch))
        return [_normalize(vector) for vector in vectors]


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    return (values[start : start + size] for start in range(0, len(values), size))


def _vectors_in_order(response: CreateEmbeddingsResponse, expected: int) -> list[list[float]]:
    if isinstance(response, str):
        raise SummaryEmbeddingError("summary embedding response is not JSON")
    if len(response.data) != expected:
        raise SummaryEmbeddingError(
            f"embedding count does not match input: expected={expected} got={len(response.data)}"
        )

    ordered = sorted(enumerate(response.data), key=_response_position)
    return [_vector(entry) for _, entry in ordered]


def _response_position(indexed: tuple[int, CreateEmbeddingsData]) -> int:
    position, entry = indexed
    return position if entry.index is None else entry.index


def _vector(entry: CreateEmbeddingsData) -> list[float]:
    if isinstance(entry.embedding, str):
        raise SummaryEmbeddingError("summary embedding returned base64, expected float list")
    if len(entry.embedding) != SUMMARY_EMBEDDING_DIMENSION:
        raise SummaryEmbeddingError(
            f"unexpected embedding dimension: expected={SUMMARY_EMBEDDING_DIMENSION} "
            f"got={len(entry.embedding)}"
        )
    return [float(value) for value in entry.embedding]


def _normalize(vector: list[float]) -> list[float]:
    """Unit length, so stored vectors stay comparable regardless of the provider's scaling."""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        raise SummaryEmbeddingError("summary embedding is a zero vector")
    return [value / norm for value in vector]
