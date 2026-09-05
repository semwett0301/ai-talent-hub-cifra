"""`SettingsTemplate` — the base every settings group extends."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The one .env for the whole repo (see .env.example) — this file lives at
# <root>/backend/common/common/core/settings/templates/base.py, hence seven levels up.
ENV_FILE = Path(__file__).resolve().parents[6] / ".env"


class SettingsTemplate(BaseSettings):
    """One group of related variables, read flat from the environment / `.env`.

    Variable names stay flat (`POSTGRES_HOST`, not `POSTGRES__HOST`): a group sets
    `env_prefix` when all its variables share one, otherwise field name = variable name.
    `extra="ignore"` because the shared `.env` also carries every other group's keys.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )
