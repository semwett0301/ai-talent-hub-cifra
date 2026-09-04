"""Shared configuration — the `settings` singleton every service reads (never `os.environ`)."""

from domain.core.settings.settings import ENV_FILE, Settings, get_settings, settings

__all__ = ["ENV_FILE", "Settings", "get_settings", "settings"]
