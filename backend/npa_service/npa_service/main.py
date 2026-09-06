"""NPA service API plus daily State Duma monitoring lifecycle."""

from contextlib import asynccontextmanager

from common.core.logging import configure_logging, get_logger
from common.core.settings import settings
from fastapi import FastAPI

from npa_service import deps
from npa_service.api.routes import health, npa

configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = deps.build_daily_monitor()
    scheduler.start()
    logger.info("npa_service started")
    try:
        yield
    finally:
        logger.info("npa_service stopping")
        scheduler.shutdown()
        await deps.close_npa_source()
        logger.info("npa_service stopped")


app = FastAPI(
    title="npa_service",
    version="0.2.0",
    lifespan=lifespan,
    root_path=settings.edge.npa_api_prefix,
)
app.include_router(health.router)
app.include_router(npa.router)
