"""`NewsDedupSettings` — models, retrieval limits, and fail-closed event policy."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class NewsDedupSettings(SettingsTemplate):
    model_config = SettingsConfigDict(env_prefix="NEWS_DEDUP_")

    extractor_model: str = "openai/gpt-5-mini"
    summary_model: str = "openai/gpt-5-mini"
    verifier_model: str = "anthropic/claude-sonnet-4.5"
    llm_batch_size: int = Field(default=70, gt=0)

    embedding_model: str = "deepvk/USER-bge-m3"
    embedding_batch_size: int = Field(default=16, gt=0)

    candidate_window_days: int = Field(default=5, gt=0)
    top_k_candidates: int = Field(default=6, gt=0)
    min_retrieval_score: float = Field(default=0.16, ge=-1.0, le=1.0)
    hard_time_tolerance_days: int = Field(default=1, ge=0)
    reject_if_any_uncertain_candidate: bool = True
