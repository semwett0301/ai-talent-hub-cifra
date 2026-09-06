"""`SettingsTemplate` — the base every settings group extends."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# <root>/backend/common/common/core/settings/templates/base.py: the repo root is six
# parents up from this file when it runs from a checkout.
_REPO_ROOT_DEPTH = 6


def _repo_env_file() -> Path | None:
    """The repo-root .env, or None when installed somewhere shallower (e.g. a /src mount)."""
    parents = Path(__file__).resolve().parents
    if len(parents) <= _REPO_ROOT_DEPTH:
        return None

    return parents[_REPO_ROOT_DEPTH] / ".env"


# The one .env for the whole repo (see .env.example); outside a checkout the environment alone.
ENV_FILE = _repo_env_file()


class SettingsTemplate(BaseSettings):
    """One group of related variables, read flat from the environment / `.env`.

    Variable names stay flat (`POSTGRES_HOST`, not `POSTGRES__HOST`): a group sets
    `env_prefix` when all its variables share one, otherwise field name = variable name.
    `extra="ignore"` because the shared `.env` also carries every other group's keys.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )
