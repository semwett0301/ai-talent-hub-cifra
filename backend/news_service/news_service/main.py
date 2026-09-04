"""news_service — consume news from RabbitMQ in batches, store them, serve list + dismiss."""

from contextlib import asynccontextmanager

from domain.core.logging import configure_logging, get_logger
from domain.core.settings import settings
from fastapi import FastAPI

from news_service import deps
from news_service.api.routes import health, news

configure_logging()
logger = get_logger(__name__)


# Startup/shutdown lifecycle: build the consumer via deps, run it alongside serving.
@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer = deps.build_consumer()
    await consumer.start()

    logger.info("news_service started")

    try:
        yield
    finally:
        logger.info("news_service stopping")

        await consumer.stop()

        logger.info("news_service stopped")


# Routers own paths from the root; nginx exposes them under settings.news_api_prefix
# and strips it before proxying. root_path tells FastAPI about that prefix so /docs
# and openapi.json resolve behind the proxy — same NEWS_API_PREFIX env var as nginx.
app = FastAPI(
    title="news_service",
    version="0.1.0",
    lifespan=lifespan,
    root_path=settings.news_api_prefix,
)
app.include_router(health.router)
app.include_router(news.router)
