"""Composition root for NPA registry, collection, LLM, and scheduling."""

from functools import lru_cache

from common.core.settings import settings

from npa_service.application.ports import ChangeSummarizer, InitialSummarizer, NpaSource
from npa_service.application.services import NpaCatalog, NpaMonitor, NpaRegistration
from npa_service.infrastructure.duma import DumaClient
from npa_service.infrastructure.llm import OpenRouterChangeSummarizer, OpenRouterInitialSummarizer
from npa_service.infrastructure.repositories import NpaRepo
from npa_service.infrastructure.scheduling import DailyMonitor
from npa_service.infrastructure.simulation import (
    SimulationChangeSummarizer,
    SimulationInitialSummarizer,
    SimulationSource,
)


@lru_cache
def get_npa_repo() -> NpaRepo:
    return NpaRepo()


@lru_cache
def get_duma_client() -> DumaClient:
    config = settings.npa
    return DumaClient(
        config.npa_request_timeout_seconds,
        config.npa_max_download_bytes,
        config.npa_user_agent,
    )


@lru_cache
def get_npa_source() -> NpaSource:
    if settings.npa.npa_simulation_enabled:
        return SimulationSource()
    return get_duma_client()


@lru_cache
def get_change_summarizer() -> ChangeSummarizer:
    if settings.npa.npa_simulation_enabled:
        return SimulationChangeSummarizer()
    return OpenRouterChangeSummarizer(
        settings.llm.openrouter_api_key,
        settings.llm.openrouter_base_url,
        settings.npa,
    )


@lru_cache
def get_initial_summarizer() -> InitialSummarizer:
    if settings.npa.npa_simulation_enabled:
        return SimulationInitialSummarizer()
    return OpenRouterInitialSummarizer(
        settings.llm.openrouter_api_key,
        settings.llm.openrouter_base_url,
        settings.npa,
    )


def get_npa_catalog() -> NpaCatalog:
    return NpaCatalog(get_npa_repo())


def get_npa_registration() -> NpaRegistration:
    return NpaRegistration(get_npa_repo(), get_npa_source(), get_initial_summarizer())


@lru_cache
def get_npa_monitor() -> NpaMonitor:
    return NpaMonitor(get_npa_repo(), get_npa_source(), get_change_summarizer())


async def close_npa_source() -> None:
    source = get_npa_source()
    if isinstance(source, DumaClient):
        await source.close()


def build_daily_monitor() -> DailyMonitor:
    return DailyMonitor(settings.npa.npa_poll_interval_seconds, get_npa_monitor().check_all)
