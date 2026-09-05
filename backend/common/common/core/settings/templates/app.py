"""`AppSettings` — who we are and how loud we are."""

from .base import SettingsTemplate


class AppSettings(SettingsTemplate):
    app_name: str = "AI Analytical Center"
    environment: str = "local"
    debug: bool = True  # DEBUG-level logging (library noise stays capped)
