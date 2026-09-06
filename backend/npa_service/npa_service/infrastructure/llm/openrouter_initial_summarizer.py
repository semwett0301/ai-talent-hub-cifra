"""Structured OpenRouter implementation for a bill's first plain-language overview."""

import httpx
from common.core.settings.templates import NpaSettings
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from openrouter.errors import OpenRouterError
from pydantic import BaseModel, Field, ValidationError

from npa_service.application.errors import ChangeModelError
from npa_service.application.ports import InitialSummarizer
from npa_service.domain import BillSnapshot, InitialSummary
from npa_service.infrastructure.llm.openrouter_change_summarizer import (
    DEFAULT_BASE_URL,
    MAX_RETRIES,
)
from npa_service.infrastructure.llm.prompts import INITIAL_SUMMARY_INPUT, INITIAL_SUMMARY_SYSTEM

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


class _InitialSummaryResponse(BaseModel):
    title: str = Field(min_length=4, max_length=90)
    summary: str = Field(min_length=20, max_length=500)


class OpenRouterInitialSummarizer(InitialSummarizer):
    def __init__(self, api_key: str | None, base_url: str | None, config: NpaSettings) -> None:
        self.__api_key = api_key
        self.__base_url = base_url or DEFAULT_BASE_URL
        self.__model_name = config.npa_change_model
        self.__max_chars = config.npa_initial_summary_max_chars
        self.__max_output_tokens = config.npa_initial_summary_max_output_tokens

    async def summarize(self, snapshot: BillSnapshot) -> InitialSummary:
        if not self.__api_key:
            raise ChangeModelError("OPENROUTER_API_KEY is required for NPA initial analysis")
        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", INITIAL_SUMMARY_SYSTEM), ("human", INITIAL_SUMMARY_INPUT)]
            )
            response = await (
                prompt | self.__model().with_structured_output(_InitialSummaryResponse)
            ).ainvoke(
                {
                    "title": snapshot.title,
                    "stage": snapshot.stage,
                    "text": snapshot.text[: self.__max_chars],
                }
            )
        except MODEL_ERRORS as error:
            raise ChangeModelError("OpenRouter NPA initial analysis failed") from error
        if (
            not isinstance(response, _InitialSummaryResponse)
            or not response.title.strip()
            or not response.summary.strip()
        ):
            raise ChangeModelError("OpenRouter returned an empty NPA initial analysis")
        return InitialSummary(title=response.title.strip(), summary=response.summary.strip())

    def __model(self) -> ChatOpenRouter:
        return ChatOpenRouter(
            model_name=self.__model_name,
            api_key=self.__api_key,
            base_url=self.__base_url,
            temperature=0.0,
            max_tokens=self.__max_output_tokens,
            max_retries=MAX_RETRIES,
            reasoning=REASONING_DISABLED,
            openrouter_provider={"require_parameters": True},
        )
