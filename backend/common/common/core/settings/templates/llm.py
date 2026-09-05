"""`LlmSettings` — which model answers, with which key, at which endpoint."""

from .base import SettingsTemplate

OPENROUTER_PREFIX = "openrouter"
OPENAI_PREFIX = "openai"


class LlmSettings(SettingsTemplate):
    """Three ways to configure one LiteLLM model, in priority order: an explicit
    `NEWS_LLM_*` provider, an OpenRouter key, an OpenAI-compatible key."""

    news_agent_model: str = "deepseek/deepseek-v4-flash"
    news_llm_provider: str | None = None
    news_llm_api_token: str | None = None
    news_llm_base_url: str | None = None

    openrouter_api_key: str | None = None
    openrouter_base_url: str | None = None
    # OpenRouter model slug without the LiteLLM ``openrouter/`` prefix, e.g. ``deepinfra/fp8``.
    openrouter_model: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    def llm_provider(self) -> str:
        """The LiteLLM model string, provider prefix included."""
        if self.news_llm_provider:
            return self.news_llm_provider
        model = self.openrouter_model or self.news_agent_model
        candidates = (
            (self.openrouter_api_key, f"{OPENROUTER_PREFIX}/{model}"),
            (self.openai_api_key, f"{OPENAI_PREFIX}/{self.news_agent_model}"),
        )
        return next(
            (provider for token, provider in candidates if token), f"{OPENROUTER_PREFIX}/{model}"
        )

    def llm_token(self) -> str | None:
        return self.news_llm_api_token or self.openrouter_api_key or self.openai_api_key

    def llm_base_url(self) -> str | None:
        return self.news_llm_base_url or self.openrouter_base_url or self.openai_base_url
