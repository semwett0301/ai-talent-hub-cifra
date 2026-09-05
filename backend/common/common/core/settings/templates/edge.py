"""`EdgeSettings` — the nginx location each service is mounted under."""

from .base import SettingsTemplate


class EdgeSettings(SettingsTemplate):
    """Kept in sync with nginx via the same env vars (see docker-compose.yml); FastAPI's
    `root_path` uses them so `/docs` and `openapi.json` resolve behind the proxy."""

    sources_api_prefix: str = "/api/sources"
    news_api_prefix: str = "/api/news"
    npa_api_prefix: str = "/api/npa"
