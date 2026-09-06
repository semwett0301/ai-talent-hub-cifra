"""Structured OpenRouter implementation of the change-summarizer port."""

import difflib

import httpx
from common.core.logging import get_logger
from common.core.settings.templates import NpaSettings
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from openrouter.errors import OpenRouterError
from pydantic import BaseModel, Field, ValidationError

from npa_service.application.errors import ChangeModelError
from npa_service.application.ports import ChangeSummarizer
from npa_service.domain import ArticleChange, ChangeSummary
from npa_service.infrastructure.llm.prompts import (
    ARTICLE_CHANGES_SYSTEM,
    CHANGE_INPUT,
    OVERALL_SUMMARY_SYSTEM,
)

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
MAX_RETRIES = 2
REASONING_DISABLED = {"enabled": False}
MODEL_ERRORS = (
    httpx.HTTPError,
    OpenRouterError,
    OutputParserException,
    ValidationError,
    RuntimeError,
    TypeError,
    ValueError,
)
logger = get_logger(__name__)


def _build_diff(previous_text: str, current_text: str) -> str:
    lines = difflib.unified_diff(
        previous_text.splitlines(),
        current_text.splitlines(),
        fromfile="previous",
        tofile="current",
        lineterm="",
        n=3,
    )
    return "\n".join(lines)


class _ArticleResponse(BaseModel):
    article: str
    summary: str
    before: str
    after: str


class _ArticleChangesResponse(BaseModel):
    article_changes: list[_ArticleResponse] = Field(default_factory=list)


class _OverallSummaryResponse(BaseModel):
    overall_summary: str


class OpenRouterChangeSummarizer(ChangeSummarizer):
    def __init__(self, api_key: str | None, base_url: str | None, config: NpaSettings) -> None:
        self.__api_key = api_key
        self.__base_url = base_url or DEFAULT_BASE_URL
        self.__model_name = config.npa_change_model
        self.__max_chars = config.npa_max_diff_chars
        self.__article_max_output_tokens = config.npa_article_changes_max_output_tokens
        self.__overall_max_output_tokens = config.npa_overall_summary_max_output_tokens

    async def summarize(self, previous_text: str, current_text: str) -> ChangeSummary:
        if not self.__api_key:
            raise ChangeModelError("OPENROUTER_API_KEY is required for NPA change analysis")
        diff = _build_diff(previous_text, current_text)
        if len(diff) > self.__max_chars:
            raise ChangeModelError(f"bill diff exceeds configured limit: chars={len(diff)}")
        logger.info("npa change analysis started: chars=%d", len(diff))
        articles_response = await self.__invoke_articles(diff)
        overall_response = await self.__invoke_overall(diff)
        logger.info(
            "npa change analysis completed: articles=%d", len(articles_response.article_changes)
        )
        articles = tuple(
            ArticleChange(row.article, row.summary, row.before, row.after)
            for row in articles_response.article_changes
        )
        return ChangeSummary(overall_response.overall_summary.strip(), articles)

    async def __invoke_articles(self, diff: str) -> _ArticleChangesResponse:
        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", ARTICLE_CHANGES_SYSTEM), ("human", CHANGE_INPUT)]
            )
            response = await (
                prompt
                | self.__model(self.__article_max_output_tokens).with_structured_output(
                    _ArticleChangesResponse
                )
            ).ainvoke({"diff": diff})
        except MODEL_ERRORS as error:
            raise ChangeModelError("OpenRouter NPA article analysis failed") from error
        if not isinstance(response, _ArticleChangesResponse):
            raise ChangeModelError("OpenRouter returned an invalid NPA article analysis")
        return response

    async def __invoke_overall(self, diff: str) -> _OverallSummaryResponse:
        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", OVERALL_SUMMARY_SYSTEM), ("human", CHANGE_INPUT)]
            )
            response = await (
                prompt
                | self.__model(self.__overall_max_output_tokens).with_structured_output(
                    _OverallSummaryResponse
                )
            ).ainvoke({"diff": diff})
        except MODEL_ERRORS as error:
            raise ChangeModelError("OpenRouter NPA overall analysis failed") from error
        if (
            not isinstance(response, _OverallSummaryResponse)
            or not response.overall_summary.strip()
        ):
            raise ChangeModelError("OpenRouter returned an empty NPA overall analysis")
        return response

    def __model(self, max_tokens: int) -> ChatOpenRouter:
        return ChatOpenRouter(
            model_name=self.__model_name,
            api_key=self.__api_key,
            base_url=self.__base_url,
            temperature=0.0,
            max_tokens=max_tokens,
            max_retries=MAX_RETRIES,
            reasoning=REASONING_DISABLED,
            openrouter_provider={"require_parameters": True},
        )
