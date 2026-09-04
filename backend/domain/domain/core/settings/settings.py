"""Application settings loaded from environment / the repo-root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The one .env for the whole repo (see .env.example) — this file lives at
# <root>/backend/domain/domain/core/settings/settings.py, hence six levels up.
ENV_FILE = Path(__file__).resolve().parents[5] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Analytical Center"
    environment: str = "local"
    debug: bool = True

    # Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "cifra"
    postgres_password: str = "cifra"
    postgres_db: str = "cifra"
    database_url: str | None = None

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    news_exchange: str = "news"

    # Edge routing — the nginx location each service is mounted under. Kept in
    # sync with nginx via the same env var (see docker-compose.yml); FastAPI's
    # root_path uses it so /docs and openapi.json resolve behind the proxy.
    sources_api_prefix: str = "/api/sources"
    news_api_prefix: str = "/api/news"

    # source_service scheduler: how often a pull source (RSS/Web) is polled when the
    # row's own `poll_interval_seconds` is null.
    source_poll_interval_seconds: int = 300

    # news_service consumer: the queue bound to the exchange, and the batch limits — a
    # batch is flushed to the DB when either is hit (size doubles as the prefetch).
    news_queue: str = "news.raw"
    news_batch_size: int = 100
    news_batch_interval_seconds: float = 60.0
    # Requeue a batch the DB write failed on (retry after one interval) vs drop it.
    news_requeue_on_store_error: bool = True

    # Telegram (MTProto user session for channel monitoring)
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_session: str = ""  # exported session string of a pre-authorized user account

    # Web-news crawler. A source is scanned independently, hence these are
    # global operational limits rather than fields on the Source ORM model.
    web_crawl_days: int = 3
    web_crawl_max_articles: int = 50
    web_crawl_llm_enabled: bool = True
    news_agent_model: str = "deepseek/deepseek-v4-flash"
    news_llm_provider: str | None = None
    news_llm_api_token: str | None = None
    news_llm_base_url: str | None = None
    openrouter_api_key: str | None = None
    openrouter_base_url: str | None = None
    openrouter_model: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    @field_validator("telegram_api_id", mode="before")
    @classmethod
    def _blank_to_none(cls, raw: object) -> object:
        """A key left empty in .env arrives as "" — treat it as "not configured"."""
        return None if raw == "" else raw

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """Sync URL used by Alembic migrations."""
        return self.async_database_url.replace("+asyncpg", "+psycopg2")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
