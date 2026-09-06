"""NPA service integration, State Duma collection, and comparison settings."""

from pydantic import Field

from .base import SettingsTemplate


class NpaSettings(SettingsTemplate):
    """Service-to-service URL plus bounded daily tracking controls."""

    npa_service_url: str = "http://localhost:8002"
    npa_poll_interval_seconds: int = Field(default=86_400, ge=5)
    npa_simulation_enabled: bool = False
    npa_request_timeout_seconds: float = Field(default=30.0, gt=0)
    npa_max_download_bytes: int = Field(default=12_000_000, ge=1_000_000)
    npa_change_model: str = "deepseek/deepseek-v4-flash-0731"
    npa_max_diff_chars: int = Field(default=120_000, ge=10_000)
    npa_article_changes_max_output_tokens: int = Field(default=1_200, ge=200, le=8_000)
    npa_overall_summary_max_output_tokens: int = Field(default=4_000, ge=500, le=16_000)
    npa_user_agent: str = "CifraNpaMonitor/1.0 (+https://sozd.duma.gov.ru/)"
