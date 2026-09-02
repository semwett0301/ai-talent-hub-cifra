"""API service — basic FastAPI entrypoint.

Skeleton only: routes/endpoints and DB wiring are added later. Uses the shared
library for configuration so the monorepo wiring is exercised from day one.
"""

from fastapi import FastAPI

from common.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
