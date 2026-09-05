"""npa_service — store legislative acts, serve list / get / create."""

from domain.core.logging import configure_logging, get_logger
from domain.core.settings import settings
from fastapi import FastAPI

from npa_service.api.routes import health, npa

configure_logging()
logger = get_logger(__name__)

# Routers own paths from the root; nginx exposes them under settings.npa_api_prefix
# and strips it before proxying. root_path tells FastAPI about that prefix so /docs
# and openapi.json resolve behind the proxy — same NPA_API_PREFIX env var as nginx.
app = FastAPI(title="npa_service", version="0.1.0", root_path=settings.npa_api_prefix)
app.include_router(health.router)
app.include_router(npa.router)

logger.info("npa_service started")
