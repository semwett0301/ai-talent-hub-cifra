"""LLM adapters for NPA version comparison."""

from npa_service.infrastructure.llm.openrouter_change_summarizer import (
    OpenRouterChangeSummarizer,
)
from npa_service.infrastructure.llm.openrouter_initial_summarizer import (
    OpenRouterInitialSummarizer,
)

__all__ = ["OpenRouterChangeSummarizer", "OpenRouterInitialSummarizer"]
