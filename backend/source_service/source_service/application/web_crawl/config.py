from __future__ import annotations

from pydantic import BaseModel


class EnvSettings(BaseModel):
    """LLM settings passed by the service composition root.

    Environment parsing belongs to ``domain.core.settings``. Keeping this a
    plain model prevents the crawler implementation from silently reading a
    second, working-directory-dependent ``.env`` file.
    """

    # ``NEWS_AGENT_*`` and ``OPENROUTER_*`` match the other baselines in this
    # workspace. ``NEWS_LLM_*`` remains available for explicit LiteLLM setup.
    news_agent_model: str = "deepseek/deepseek-v4-flash"
    news_llm_provider: str | None = None
    news_llm_api_token: str | None = None
    news_llm_base_url: str | None = None
    news_crawl_log_level: str = "INFO"

    openrouter_api_key: str | None = None
    openrouter_base_url: str | None = None
    # OpenRouter model slug, without the LiteLLM ``openrouter/`` prefix.
    # Examples: ``deepinfra/fp8`` or ``google/gemini-2.5-flash``.
    openrouter_model: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    def llm_provider(self) -> str:
        if self.news_llm_provider:
            return self.news_llm_provider
        model = self.openrouter_model or self.news_agent_model
        candidates = (
            (self.openrouter_api_key, f"openrouter/{model}"),
            (self.openai_api_key, f"openai/{self.news_agent_model}"),
        )
        return next((provider for token, provider in candidates if token), f"openrouter/{model}")

    def llm_token(self) -> str | None:
        return self.news_llm_api_token or self.openrouter_api_key or self.openai_api_key

    def llm_base_url(self) -> str | None:
        return self.news_llm_base_url or self.openrouter_base_url or self.openai_base_url
