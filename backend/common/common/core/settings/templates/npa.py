"""`NpaSettings` — how `news_service` reaches `npa_service` over HTTP."""

from .base import SettingsTemplate


class NpaSettings(SettingsTemplate):
    """Where the escalation endpoint posts new acts; compose points it at the internal
    service name, so the default only serves a local run."""

    npa_service_url: str = "http://localhost:8002"
