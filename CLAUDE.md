# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

AI Analytical Center — an AI intelligence hub that collects, structures, and
summarizes industry news for PR/GR teams. Hackathon MVP. See `README.md` for the
product brief.

**Current state: skeleton.** One service with a basic FastAPI startup plus a
thin shared library (config + logging). Domain code (DB, models, schemas, LLM),
migrations, tests, and more services are added on top as the app grows.

## Layout

uv workspace monorepo. A single shared package `common/` at the root (the root
`pyproject.toml` is that package **and** the workspace root); services live under
`services/`.

```
common/                 # shared package, imported as `common`
  core/    config (pydantic-settings), logging
services/
  api/                  # package: cifra-api — basic FastAPI service
    app/main.py         # index only: `/` and `/health`
    Dockerfile          # the one Dockerfile for now
    pyproject.toml
docker-compose.yml      # root: postgres + api
pyproject.toml          # root = the `common` package + workspace (members = services/*)
```

`common` grows to hold shared DB/models/schemas/LLM code as those are introduced.
`data/`, `migrations/`, and test dirs are intentionally absent for now.

## Architecture rules

- Shared code (config, and later db, models, schemas, LLM) lives in `common`.
  Service dirs hold only that service's own logic.
- When models are added, they live **only** in `common.models`; one shared
  Postgres, one Alembic history.
- **No cross-service imports** — services share via `common`.
- Endpoints stay thin; keep LLM and network I/O in services / `common`.
- Never return ORM objects raw — map through Pydantic schemas.

## Conventions

- **Async everywhere** on the request path.
- **Config** only through `common.core.config.settings` — never read
  `os.environ`; add a field to `Settings`.
- **Logging** via `common.core.logging.get_logger` (structlog). No `print`.
- Keep dependencies minimal — only add a package to a `pyproject.toml` when code
  actually imports it.
- Line length 100; lint/format with `ruff` (see `pyproject.toml`).

## Commands

Uses **uv** — one shared venv + lockfile at the root.

```bash
uv sync --all-packages            # install common + all services + dev tools
uv sync --package cifra-api       # just the api service

# Run the API (from services/api)
uv run uvicorn app.main:app --reload

# Quality gates (CI pins ruff 0.14.0)
uvx ruff@0.14.0 check .
uvx ruff@0.14.0 format --check .

# Full stack
docker compose up --build         # from repo root
```

CI (`.github/workflows/ci.yml`) runs the Ruff lint + format check only.

## When adding features

- **New service** → create `services/<name>/` with a `pyproject.toml` (depend on
  `common`), an `app/` package, and a `Dockerfile`; add a block to
  `docker-compose.yml`. The workspace glob (`services/*`) picks it up.
- **Shared code** (DB session, models, schemas, LLM) → add under `common/` and
  its deps to the root `pyproject.toml`.
- **Migrations** → introduce Alembic (`migrations/`) with a single shared
  history once models exist; only one service runs `upgrade head` on startup.
- **Tests** → per-service unit tests, or top-level e2e — added when there's
  behavior worth testing.

## Guardrails

- Do not commit `.env`, `*.session`, or API keys.
- Out of scope: production load, extra modalities, infosec.
- Don't call the LLM from tests or CI.
- Prefer editing existing code over adding parallel structures.

## Skills & rules

Reusable stack know-how is under `.claude/skills/` (official LangChain skills).
Project rules are in `.claude/rules/` (`00-conventions`, `20-git`, `40-monorepo`).
