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
from news_service.domain.dedup import (
    EventSummary,
    MembershipDecision,
    NewsTarget,
    Precluster,
)
from news_service.domain.dedup.membership_decision import Decision
from news_service.infrastructure.dedup.prompts import (
    PRECLUSTER_ALIGNMENT_SYSTEM,
    PRIMARY_EVENT_SYSTEM,
    SUMMARY_SYSTEM,
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
NO_EVENT_SUMMARY = "No concrete primary event identified."
MAX_RETRIES = 2

logger = get_logger(__name__)


class _EvidenceSpan(BaseModel):
    field: str
    quote: str


class _EventTime(BaseModel):
    start: str | None = None
    end: str | None = None
    precision: str = "unknown"
    source: str = "unknown"


class _Quantity(BaseModel):
    type: str
    value: str
    unit: str | None = None


class _EventExtraction(BaseModel):
    primary_event_found: bool
    primary_event_mention: str | None = None
    event_type: str | None = None
    actors: list[str] = Field(default_factory=list)
    action: str | None = None
    objects: list[str] = Field(default_factory=list)
    location: str | None = None
    event_time: _EventTime | None = None
    quantities: list[_Quantity] = Field(default_factory=list)
    lifecycle_stage: str | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    evidence: list[_EvidenceSpan] = Field(default_factory=list)
    background_events: list[str] = Field(default_factory=list)
    critical_unknowns: list[str] = Field(default_factory=list)


class _SummaryResponse(BaseModel):
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
        self.__extractor = self.__make_model(config.extractor_model)
        self.__summarizer = self.__make_model(config.summary_model)
        self.__verifier = self.__make_model(config.verifier_model)

    async def summarize(self, items: list[NewsTarget]) -> list[EventSummary]:
        logger.info("event extraction started: items=%d", len(items))
        extractions = await self.__extract(items)
        logger.info("event extraction completed: items=%d", len(extractions))
        payloads = [
            {
                "source_item": target.news.model_dump(mode="json"),
                "extraction": extraction.model_dump(mode="json"),
            }
            for target, extraction in zip(items, extractions, strict=True)
        ]
        logger.info("event summaries started: items=%d", len(items))
        generated = await self.__invoke(
            _BatchSpec(self.__summarizer, SUMMARY_SYSTEM, payloads, _SummaryResponse)
        )
        if len(generated) != len(items):
            raise EventModelError("event summary count does not match input count")
        logger.info("event summaries completed: items=%d", len(generated))
        return [
            _build_summary(target, extraction, response)
            for target, extraction, response in zip(items, extractions, generated, strict=True)
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

    async def __extract(self, items: list[NewsTarget]) -> list[_EventExtraction]:
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
        return [response or _EventExtraction(primary_event_found=False) for response in responses]

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
            raise EventModelError(f"event model setup failed: model={model}") from error


def _chunks(values: list[dict[str, str]], size: int) -> Iterable[list[dict[str, str]]]:
    return (values[start : start + size] for start in range(0, len(values), size))


def _build_summary(
    target: NewsTarget,
    extraction: _EventExtraction,
    response: _SummaryResponse | None,
) -> EventSummary:
    text = (
        response.summary.strip() if response and response.summary.strip() else _fallback(extraction)
    )
    return EventSummary(
        news_id=target.news_id,
        url=target.news.url,
        text=text,
        extraction=extraction.model_dump(mode="json"),
        published_at=target.news.published_at,
    )


def _fallback(extraction: _EventExtraction) -> str:
    if not extraction.primary_event_found:
        return NO_EVENT_SUMMARY
    event_time = extraction.event_time.start if extraction.event_time else ""
    parts = [
        ", ".join(extraction.actors),
        extraction.action or "",
        ", ".join(extraction.objects),
        extraction.location or "",
        event_time or "",
    ]
    return (
        " ".join(part for part in parts if part).strip()
        or extraction.primary_event_mention
        or NO_EVENT_SUMMARY
    )


def _precluster_payload(precluster: Precluster) -> dict[str, Any]:
    return {
        "anchor_event_summaries": [_summary_payload(summary) for summary in precluster.anchors],
        "candidate_event_summaries": [
            _summary_payload(summary) for summary in precluster.candidates
        ],
    }


def _summary_payload(summary: EventSummary) -> dict[str, Any]:
    return {
        "news_id": str(summary.news_id),
        "summary": summary.text,
        "extraction": summary.extraction,
    }


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
