"""`TelegramSettings` — the MTProto user session that monitors channels."""

from pydantic import field_validator
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class TelegramSettings(SettingsTemplate):
    """All three empty = the Telegram collector is disabled."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    api_id: int | None = None
    api_hash: str | None = None
    session: str = ""  # exported session string of a pre-authorized user account

    @field_validator("api_id", mode="before")
    @classmethod
    def _blank_to_none(cls, raw: object) -> object:
        """A key left empty in .env arrives as "" — treat it as "not configured"."""
        return None if raw == "" else raw
