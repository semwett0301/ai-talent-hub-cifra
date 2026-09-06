"""`SettingsTemplate` — the base every settings group extends."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsTemplate(BaseSettings):
    """One group of related variables, read flat from the process environment.

    No `.env` is read here: Docker Compose (and, on the host, `set -a; source .env`)
    puts the repo-root `.env` into the environment, so the code stays ignorant of where
    that file lives. `extra="ignore"` because the environment carries every other
    group's keys too; a group sets `env_prefix` when all its variables share one.
    """

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)
