"""`NewsDedupSettings` — models, retrieval limits, and fail-closed event policy."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class NewsDedupSettings(SettingsTemplate):
    model_config = SettingsConfigDict(env_prefix="NEWS_DEDUP_")

    extractor_model: str = "openai/gpt-5-mini"
    verifier_model: str = "deepseek/deepseek-v4-flash-0731"
    # Concurrent structured calls; OpenRouter reserves credits per in-flight request.
    llm_batch_size: int = Field(default=20, gt=0)

    embedding_model: str = "baai/bge-m3"
    embedding_batch_size: int = Field(default=64, gt=0)

    candidate_window_days: int = Field(default=3, gt=0)
    top_k_candidates: int = Field(default=6, gt=0)
    min_retrieval_score: float = Field(default=0.16, ge=-1.0, le=1.0)
    reject_if_any_uncertain_candidate: bool = True
