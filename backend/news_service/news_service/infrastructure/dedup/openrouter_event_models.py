"""LangChain/OpenRouter implementation of the event-model port."""

import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

import httpx
from common.core.logging import get_logger
from common.core.settings import NewsDedupSettings
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from openrouter.errors import OpenRouterError
from pydantic import BaseModel, Field, ValidationError

from news_service.application.errors import EventModelError
from news_service.application.ports import EventModels
from news_service.domain.event_cluster import Decision, MembershipDecision, Precluster
from news_service.domain.event_summary import EventSummary, NewsTarget
from news_service.infrastructure.dedup.prompts import (
    PRECLUSTER_ALIGNMENT_SYSTEM,
    PRIMARY_EVENT_SYSTEM,
)

MODEL_ERRORS = (
    httpx.HTTPError,
    OpenRouterError,
    OutputParserException,
    ValidationError,
    RuntimeError,
    TypeError,
    ValueError,
)
MAX_RETRIES = 2
DETERMINISTIC_TEMPERATURE = 0.0

logger = get_logger(__name__)


class _EventExtraction(BaseModel):
    primary_event_found: bool
    summary: str


class _MemberVerdict(BaseModel):
    news_id: uuid.UUID
    decision: Decision
    hard_conflicts: list[str] = Field(default_factory=list)
    critical_unknowns: list[str] = Field(default_factory=list)
    rationale: str


class _PreclusterResponse(BaseModel):
    member_decisions: list[_MemberVerdict] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _BatchSpec[T: BaseModel]:
    model: BaseChatModel
    system_prompt: str
    payloads: list[dict[str, Any]]
    schema: type[T]


class OpenRouterEventModels(EventModels):
    def __init__(
        self, api_key: str | None, base_url: str | None, config: NewsDedupSettings
    ) -> None:
        if not api_key:
            raise EventModelError("OPENROUTER_API_KEY is required for news deduplication")
        self.__api_key = api_key
        self.__base_url = base_url
        self.__batch_size = config.llm_batch_size
        # GPT-5 providers reject `temperature`, and `require_parameters` would then route nowhere.
        self.__extractor = self.__make_model(config.extractor_model, temperature=None)
        self.__verifier = self.__make_model(config.verifier_model, DETERMINISTIC_TEMPERATURE)

    async def summarize(self, items: list[NewsTarget]) -> list[EventSummary]:
        logger.info("event summaries started: items=%d", len(items))
        payloads = [
            {
                "item": target.news.model_dump(mode="json"),
                "publication_time": target.news.published_at,
            }
            for target in items
        ]
        responses = await self.__invoke(
            _BatchSpec(self.__extractor, PRIMARY_EVENT_SYSTEM, payloads, _EventExtraction)
        )
        if len(responses) != len(items):
            raise EventModelError("event summary count does not match input count")
        logger.info("event summaries completed: items=%d", len(responses))
        return [
            _build_summary(target, response)
            for target, response in zip(items, responses, strict=True)
        ]

    async def align(
        self, preclusters: list[Precluster]
    ) -> list[dict[uuid.UUID, MembershipDecision]]:
        payloads = [_precluster_payload(precluster) for precluster in preclusters]
        logger.info("event alignment started: preclusters=%d", len(preclusters))
        responses = await self.__invoke(
            _BatchSpec(self.__verifier, PRECLUSTER_ALIGNMENT_SYSTEM, payloads, _PreclusterResponse)
        )
        if len(responses) != len(preclusters):
            raise EventModelError("event alignment count does not match precluster count")
        logger.info("event alignment completed: preclusters=%d", len(responses))
        return [_membership_map(response) for response in responses]

    async def __invoke[T: BaseModel](self, spec: _BatchSpec[T]) -> list[T | None]:
        inputs = [
            {"payload": json.dumps(payload, ensure_ascii=False, default=str)}
            for payload in spec.payloads
        ]
        if not inputs:
            return []
        responses: list[T | None] = []
        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", spec.system_prompt), ("human", "Input JSON:\n{payload}")]
            )
            chain = prompt | spec.model.with_structured_output(spec.schema)
            for batch in _chunks(inputs, self.__batch_size):
                generated = await chain.abatch(batch, config={"max_concurrency": self.__batch_size})
                responses.extend(cast(list[T | None], generated))
        except MODEL_ERRORS as error:
            raise EventModelError(f"event model batch failed: items={len(inputs)}") from error
        return responses

    def __make_model(self, model: str, temperature: float | None) -> ChatOpenRouter:
        try:
            return ChatOpenRouter(
                model_name=model,
                api_key=self.__api_key,
                base_url=self.__base_url,
                temperature=temperature,
                max_retries=MAX_RETRIES,
                openrouter_provider={"require_parameters": True},
            )
        except MODEL_ERRORS as error:
            raise EventModelError(f"event model setup failed: model={model}") from error


def _chunks(values: list[dict[str, str]], size: int) -> Iterable[list[dict[str, str]]]:
    return (values[start : start + size] for start in range(0, len(values), size))


def _build_summary(target: NewsTarget, response: _EventExtraction | None) -> EventSummary:
    if response is None or not response.summary.strip():
        raise EventModelError(f"event summary missing or empty: news_id={target.news_id}")
    return EventSummary(
        news_id=target.news_id,
        url=target.news.url,
        text=response.summary.strip(),
        has_primary_event=response.primary_event_found,
        published_at=target.news.published_at,
    )


def _precluster_payload(precluster: Precluster) -> dict[str, Any]:
    return {
        "anchor_event_summaries": [_summary_payload(summary) for summary in precluster.anchors],
        "candidate_event_summaries": [
            _summary_payload(summary) for summary in precluster.candidates
        ],
    }


def _summary_payload(summary: EventSummary) -> dict[str, Any]:
    return {"news_id": str(summary.news_id), "summary": summary.text}


def _membership_map(
    response: _PreclusterResponse | None,
) -> dict[uuid.UUID, MembershipDecision]:
    if response is None:
        return {}
    return {
        verdict.news_id: MembershipDecision(
            verdict.decision,
            tuple(verdict.hard_conflicts),
            tuple(verdict.critical_unknowns),
        )
        for verdict in response.member_decisions
    }
