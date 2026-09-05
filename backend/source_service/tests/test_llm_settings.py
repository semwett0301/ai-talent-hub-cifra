from common.core.settings import LlmSettings


def test_openrouter_model_slug_is_adapted_to_litellm_provider_name():
    settings = LlmSettings(
        news_llm_provider="",
        openrouter_api_key="test-key",
        openrouter_model="deepinfra/fp8",
    )

    assert settings.llm_provider() == "openrouter/deepinfra/fp8"
