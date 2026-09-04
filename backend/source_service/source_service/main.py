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
    # Startup — build infra, connect, then load + start the runtime registry.
    rabbit = deps.build_rabbit()
    await rabbit.connect()

    telegram = deps.build_telegram_collector(rabbit)
    await telegram.start()

    # Registry: CRUD reaches it via app.state to (un)schedule/(un)subscribe live.
    registry = deps.build_registry(rabbit, telegram)
    await registry.load()

    registry.start()

    app.state.registrar = registry

    logger.info("source_service started")

    # Serve until shutdown, then tear down
    try:
        yield
    finally:
        registry.shutdown()
        await telegram.stop()
        await rabbit.close()


# Routers own paths from the root; nginx exposes them under settings.sources_api_prefix
# and strips it before proxying. root_path tells FastAPI about that prefix so /docs
# and the generated openapi.json use the right absolute URLs — kept in sync with
# nginx via the same SOURCES_API_PREFIX env var (see docker-compose.yml).
app = FastAPI(
    title="source_service",
    version="0.1.0",
    lifespan=lifespan,
    root_path=settings.sources_api_prefix,
)
app.include_router(health.router)
app.include_router(sources.router)
