"""`NewsRankingSettings` — model and batching knobs for cluster relevance ranking."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class NewsRankingSettings(SettingsTemplate):
    model_config = SettingsConfigDict(env_prefix="NEWS_RANKING_")

    impact_model: str = "deepseek/deepseek-v4-flash-0731"
    llm_batch_size: int = Field(default=70, gt=0)
