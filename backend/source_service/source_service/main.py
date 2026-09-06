"""source_service — CRUD sources, collect news (stubs), publish to RabbitMQ."""

# Imports
from contextlib import asynccontextmanager

from common.core.logging import configure_logging, get_logger
from common.core.settings import settings
from fastapi import FastAPI

from source_service import deps
from source_service.api.errors import install_error_handlers
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

    # One HTTP fetcher for every RSS feed and article pull.
    page_fetcher = deps.build_page_fetcher()
    await page_fetcher.start()

    # One headless browser for every WEB source pull.
    page_crawler = deps.build_page_crawler()
    await page_crawler.start()

    # Registry: CRUD reaches it via app.state to (un)schedule/(un)subscribe live.
    scheduler = deps.build_job_scheduler()
    registry = deps.build_registry(rabbit, scheduler, telegram, (page_fetcher, page_crawler))
    await registry.load()

    scheduler.start()
    app.state.registrar = registry

    logger.info("source_service started")

    # Serve until shutdown, then tear down
    try:
        yield
    finally:
        logger.info("source_service stopping")

        scheduler.shutdown()
        await telegram.stop()
        await page_crawler.close()
        await page_fetcher.close()
        await rabbit.close()

        logger.info("source_service stopped")


# Routers own paths from the root; nginx exposes them under settings.edge.sources_api_prefix
# and strips it before proxying. root_path tells FastAPI about that prefix so /docs
# and the generated openapi.json use the right absolute URLs — kept in sync with
# nginx via the same SOURCES_API_PREFIX env var (see docker-compose.yml).
app = FastAPI(
    title="source_service",
    version="0.1.0",
    lifespan=lifespan,
    root_path=settings.edge.sources_api_prefix,
)
app.include_router(health.router)
app.include_router(sources.router)
install_error_handlers(app)
