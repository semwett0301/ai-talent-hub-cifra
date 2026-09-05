"""`NewsConsumerSettings` — how `news_service` drains the `news` exchange."""

from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class NewsConsumerSettings(SettingsTemplate):
    """A batch is flushed to the DB when either limit is hit; `batch_size` doubles as the
    prefetch count."""

    model_config = SettingsConfigDict(env_prefix="NEWS_")

    queue: str = "news.raw"  # the queue bound to the exchange
    batch_size: int = 100
    batch_interval_seconds: float = 60.0
    # Requeue a batch the DB write failed on (retry after one interval) vs drop it.
    requeue_on_store_error: bool = True
