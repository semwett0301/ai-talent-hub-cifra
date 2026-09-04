"""source_service — CRUD sources, collect news (stubs), publish to RabbitMQ."""

# Imports
from contextlib import asynccontextmanager

from common.core.logging import configure_logging, get_logger
from common.settings import settings
from fastapi import FastAPI

from source_service import deps
from source_service.api.routes import health, sources

# Logging setup + module logger
configure_logging()
logger = get_logger(__name__)


# Startup/shutdown lifecycle: build collaborators via deps, connect infra, start
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    rabbit = deps.build_rabbit()
    await rabbit.connect()
    scheduler = deps.build_scheduler(rabbit)
    subscriptions = deps.build_subscriptions()
    await scheduler.load()
    await subscriptions.load()
    scheduler.start()
    logger.info("source_service started")

    # Serve until shutdown, then tear down
    try:
        yield
    finally:
        scheduler.shutdown()
        await rabbit.close()


# root_path (/api/sources behind nginx) fixes OpenAPI/docs links; routers own paths from root.
app = FastAPI(
    title="source_service",
    version="0.1.0",
    lifespan=lifespan,
    root_path=settings.api_root_path,
)
app.include_router(health.router)
app.include_router(sources.router)
