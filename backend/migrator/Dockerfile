# Migrator image — one-shot `alembic upgrade head`, then exit. Build context = ./backend.
# Multi-stage: the builder uses uv to resolve the workspace lockfile into a `.venv`
# with the migrator's runtime deps only (common + Alembic + psycopg2; the `autogen`
# group of services is excluded, so no service package). Only that venv — plus the
# Alembic config/migrations, run in-place — lands on a clean python:3.12-slim runtime.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Workspace root + lockfile, then the one first-party package uv builds (common).
COPY pyproject.toml uv.lock ./
COPY common ./common
COPY migrator ./migrator

RUN uv sync --frozen --package migrator --no-default-groups --no-editable

# Runtime: Python + the prebuilt venv + this runner's Alembic config/migrations.
FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/migrator
COPY --from=builder /app/.venv /app/.venv
COPY migrator/alembic.ini ./alembic.ini
COPY migrator/migrations ./migrations

CMD ["alembic", "upgrade", "head"]
