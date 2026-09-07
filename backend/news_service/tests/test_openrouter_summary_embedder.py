import math

import pytest
from common.schemas.news_event_state import SUMMARY_EMBEDDING_DIMENSION
from news_service.application.errors import SummaryEmbeddingError
from news_service.infrastructure.dedup.openrouter_summary_embedder import (
    _normalize,
    _vectors_in_order,
)
from openrouter.operations import CreateEmbeddingsData, CreateEmbeddingsResponseBody


def _vector(seed: float) -> list[float]:
    return [seed] * SUMMARY_EMBEDDING_DIMENSION


def _response(*entries: CreateEmbeddingsData) -> CreateEmbeddingsResponseBody:
    return CreateEmbeddingsResponseBody(data=list(entries), model="baai/bge-m3", object="list")


def test_vectors_follow_the_response_index_not_the_wire_order():
    response = _response(
        CreateEmbeddingsData(embedding=_vector(2.0), object="embedding", index=1),
        CreateEmbeddingsData(embedding=_vector(1.0), object="embedding", index=0),
    )

    first, second = _vectors_in_order(response, expected=2)

    assert (first[0], second[0]) == (1.0, 2.0)


def test_wrong_dimension_is_rejected():
    response = _response(CreateEmbeddingsData(embedding=[1.0, 2.0], object="embedding", index=0))

    with pytest.raises(SummaryEmbeddingError, match="unexpected embedding dimension"):
        _vectors_in_order(response, expected=1)


def test_count_mismatch_is_rejected():
    response = _response(CreateEmbeddingsData(embedding=_vector(1.0), object="embedding", index=0))

    with pytest.raises(SummaryEmbeddingError, match="embedding count does not match"):
        _vectors_in_order(response, expected=2)


def test_normalize_yields_unit_length():
    normalized = _normalize([3.0, 4.0])

    assert math.isclose(math.hypot(*normalized), 1.0)
    assert normalized == [0.6, 0.8]
