"""source_service — CRUD sources, collect news (stubs), publish to RabbitMQ."""

# Imports
from contextlib import asynccontextmanager

from common.core.logging import configure_logging, get_logger
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


# App assembly and routes
app = FastAPI(title="source_service", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
# Served at /sources; nginx exposes it publicly as /api/sources.
app.include_router(sources.router)
