"""OpenRouter impact judge and cross-encoder reranker for event clusters."""

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Literal, cast

import httpx
from common.core.logging import get_logger
from common.core.settings import NewsRankingSettings
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from openrouter.errors import OpenRouterError
from pydantic import BaseModel, Field, ValidationError

from news_service.application.errors import RankingModelError
from news_service.application.ports import RankingModels
from news_service.domain.ranking import (
    ClusterRankingTarget,
    CompanyProfile,
    ImpactAssessment,
)
from news_service.infrastructure.ranking.prompts import IMPACT_SYSTEM

UrgencyBasis = Literal[
    "not_urgent",
    "over_30_days",
    "within_4_30_days",
    "within_3_days",
    "already_happened",
    "breaking",
]
URGENCY_SCORE: dict[UrgencyBasis, int] = {
    "not_urgent": 0,
    "over_30_days": 1,
    "within_4_30_days": 2,
    "within_3_days": 3,
    "already_happened": 3,
    "breaking": 3,
}
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_RETRIES = 2
MODEL_ERRORS = (
    httpx.HTTPError,
    OpenRouterError,
    OutputParserException,
    ValidationError,
    RuntimeError,
    TypeError,
    ValueError,
    KeyError,
)

logger = get_logger(__name__)


class _ImpactResponse(BaseModel):
    finance_score: int = Field(ge=0, le=3)
    finance_reason: str
    reputation_score: int = Field(ge=0, le=3)
    reputation_reason: str
    technology_score: int = Field(ge=0, le=3)
    technology_reason: str
    competition_score: int = Field(ge=0, le=3)
    competition_reason: str
    urgency_basis: UrgencyBasis
    urgency_reason: str


class OpenRouterRankingModels(RankingModels):
    def __init__(
        self,
        api_key: str | None,
        base_url: str | None,
        config: NewsRankingSettings,
    ) -> None:
        if not api_key:
            raise RankingModelError("OPENROUTER_API_KEY is required for news ranking")
        self.__api_key = api_key
        self.__base_url = (base_url or DEFAULT_OPENROUTER_BASE_URL).rstrip("/")
        self.__impact_model = self.__make_model(config.impact_model)
        self.__reranker_model = config.reranker_model
        self.__llm_batch_size = config.llm_batch_size
        self.__reranker_batch_size = config.reranker_batch_size
        self.__timeout = config.reranker_timeout_seconds
        self.__max_cluster_chars = config.max_cluster_chars

    async def assess(
        self,
        company: CompanyProfile,
        targets: list[ClusterRankingTarget],
        evaluated_at: datetime,
    ) -> list[ImpactAssessment]:
        if not targets:
            return []
        logger.info("cluster impact assessment started: clusters=%d", len(targets))
        inputs = [
            {"payload": json.dumps(_impact_payload(target, evaluated_at), ensure_ascii=False)}
            for target in targets
        ]
        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", _impact_system(company)), ("human", "Input JSON:\n{payload}")]
            )
            chain = prompt | self.__impact_model.with_structured_output(_ImpactResponse)
            responses = await _invoke_batches(chain, inputs, self.__llm_batch_size)
        except MODEL_ERRORS as error:
            raise RankingModelError(
                f"cluster impact assessment failed: clusters={len(targets)}"
            ) from error
        logger.info("cluster impact assessment completed: clusters=%d", len(responses))
        return [_to_assessment(response) for response in responses]

    async def rerank(
        self, company: CompanyProfile, targets: list[ClusterRankingTarget]
    ) -> list[float]:
        if not targets:
            return []
        logger.info("cluster semantic reranking started: clusters=%d", len(targets))
        query = company.reranker_query
        documents = [target.document[: self.__max_cluster_chars] for target in targets]
        try:
            scores = await self.__rerank_batches(query, documents)
        except MODEL_ERRORS as error:
            raise RankingModelError(
                f"cluster semantic reranking failed: clusters={len(targets)}"
            ) from error
        logger.info("cluster semantic reranking completed: clusters=%d", len(scores))
        return scores

    async def __rerank_batches(self, query: str, documents: list[str]) -> list[float]:
        scores: list[float] = []
        async with httpx.AsyncClient(timeout=self.__timeout) as client:
            for batch in _chunks(documents, self.__reranker_batch_size):
                scores.extend(await self.__rerank_batch(client, query, batch))
        return scores

    async def __rerank_batch(
        self, client: httpx.AsyncClient, query: str, documents: list[str]
    ) -> list[float]:
        response = await client.post(
            f"{self.__base_url}/rerank",
            headers={"Authorization": f"Bearer {self.__api_key}"},
            json={
                "model": self.__reranker_model,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            },
        )
        response.raise_for_status()
        payload = response.json()
        return _reranker_scores(payload, len(documents))

    def __make_model(self, model: str) -> ChatOpenRouter:
        try:
            return ChatOpenRouter(
                model_name=model,
                api_key=self.__api_key,
                base_url=self.__base_url,
                temperature=0.0,
                max_retries=MAX_RETRIES,
                openrouter_provider={"require_parameters": True},
            )
        except MODEL_ERRORS as error:
            raise RankingModelError(f"ranking model setup failed: model={model}") from error


async def _invoke_batches(chain, inputs: list[dict[str, str]], size: int) -> list[_ImpactResponse]:
    responses: list[_ImpactResponse] = []
    for batch in _chunks(inputs, size):
        generated = await chain.abatch(batch, config={"max_concurrency": size})
        responses.extend(cast(list[_ImpactResponse], generated))
    return responses


def _impact_system(company: CompanyProfile) -> str:
    return f"{IMPACT_SYSTEM}\n\n{company.reranker_query}"


def _impact_payload(target: ClusterRankingTarget, evaluated_at: datetime) -> dict[str, object]:
    return {
        "cluster_id": str(target.cluster_id),
        "evaluated_at": evaluated_at.isoformat(),
        "published_at": target.published_at.isoformat() if target.published_at else None,
        "summaries": target.summaries,
        "event_extractions": target.extractions,
        "member_count": target.member_count,
    }


def _to_assessment(response: _ImpactResponse) -> ImpactAssessment:
    return ImpactAssessment(
        response.finance_score,
        response.finance_reason,
        response.reputation_score,
        response.reputation_reason,
        response.technology_score,
        response.technology_reason,
        response.competition_score,
        response.competition_reason,
        response.urgency_basis,
        response.urgency_reason,
        URGENCY_SCORE[response.urgency_basis],
        response.model_dump(mode="json"),
    )


def _reranker_scores(payload: object, expected: int) -> list[float]:
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("unexpected OpenRouter reranker response")
    scores = [0.0] * expected
    seen: set[int] = set()
    for row in payload["results"]:
        index = int(row["index"])
        score = float(row["relevance_score"])
        if index < 0 or index >= expected or index in seen:
            raise ValueError("invalid OpenRouter reranker result index")
        if score < 0.0 or score > 1.0:
            raise ValueError("OpenRouter reranker score is outside 0..1")
        seen.add(index)
        scores[index] = score
    if len(seen) != expected:
        raise ValueError("reranker response count does not match document count")
    return scores


def _chunks[T](values: list[T], size: int) -> Iterable[list[T]]:
    return (values[start : start + size] for start in range(0, len(values), size))
