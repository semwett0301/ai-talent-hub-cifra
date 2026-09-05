"""`PostgresSettings` — the one database every service shares."""

from pydantic import Field, computed_field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate

ASYNC_DRIVER = "+asyncpg"
SYNC_DRIVER = "+psycopg2"


class PostgresSettings(SettingsTemplate):
    """`POSTGRES_*` pieces, or one `DATABASE_URL` that overrides them all."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = "localhost"
    port: int = 5432
    user: str = "cifra"
    password: str = "cifra"
    db: str = "cifra"
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql{ASYNC_DRIVER}://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """Sync URL used by Alembic migrations."""
        return self.async_database_url.replace(ASYNC_DRIVER, SYNC_DRIVER)
