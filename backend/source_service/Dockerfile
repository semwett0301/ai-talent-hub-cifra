# Source service image (FastAPI + Uvicorn). Build context = ./backend.
# Multi-stage: the builder uses uv to resolve the workspace lockfile into a
# self-contained `.venv` (`--no-editable` copies our code into site-packages), then
# only that venv lands on a clean python:3.12-slim runtime — no uv binary, no source
# duplication. Migrations are not here — the `migrator` service owns the schema history.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Workspace root + lockfile, the shared `common` package, then the service.
COPY pyproject.toml uv.lock ./
COPY common ./common
COPY source_service ./source_service

RUN uv sync --frozen --package source-service --no-dev --no-editable

# Runtime: just Python + the prebuilt venv (which already contains our code).
FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

EXPOSE 8000
CMD ["uvicorn", "source_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
