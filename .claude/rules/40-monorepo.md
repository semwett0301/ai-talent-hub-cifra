# Repo structure

Backend and frontend are separated; the root holds only deployment and shared
repo files.

```
backend/     all Python — its own uv workspace (root pyproject = virtual workspace root, no package)
  common/    shared kernel, its own pyproject; package at common/common (imported as `common`)
             core/ (settings/logging/db/errors/llm/rabbit subpackages) + entities/ (business shapes) + schemas/ (shared ORM models)
  source_service/, news_service/, migrator/   one package per service, siblings of common (no services/ wrapper)
frontend/    React SPA (Vite, TypeScript, React Router) — built to static files
nginx/       edge image: serves static SPA + proxies /api/* → services, /logs/* → dozzle
docker-compose.yml, README, CLAUDE.md, .github, .claude   ← root
```

## Backend

- The backend is a **uv workspace** rooted at `backend/`. `backend/pyproject.toml`
  is a **virtual workspace root** — it declares no package of its own, only
  `[tool.uv.workspace]` members plus the shared dev tooling (ruff/mypy/pytest). Run
  uv from `backend/`.
- One shared kernel only — `backend/common/`, a regular workspace member with its
  own `pyproject.toml` (package code at `common/common/`). Do not add a `libs/`
  wrapper.
- **The DB is one for all services, so ORM schemas are shared.** Every ORM model
  lives in `common/schemas/` (re-exported from `common.schemas`), not per service —
  every service and the `migrator` import the same tables. The Alembic history is
  centralized in the `migrator`, which imports `common.schemas`.
- **`common` holds:** `core/` (settings, logging, db, llm infra — `LlmCallBudget`
  caps LLM calls per run; never hand-roll a semaphore in a service), `entities/` (business
  shapes, grouped by domain — e.g. `entities/news`), and `schemas/` (shared ORM
  models). Service dirs hold only that service's own logic (use cases, ports,
  collectors, routes). **No cross-service imports** — services communicate only
  through `common` and the message bus, never importing each other; the `migrator`
  imports only `common.schemas`.
- Each service is a sibling dir of `common` with its own **uniquely named**
  importable package (e.g. `source_service`, not a generic `app`), `pyproject.toml`
  (depending on `common`), and `Dockerfile`. New service = copy
  `backend/source_service`, add it to `[tool.uv.workspace] members` in
  `backend/pyproject.toml`, and add a block to `docker-compose.yml`.
- **Project names match the directory — no `cifra-` (or any) prefix.** The
  `[project] name` is the folder name (`source-service`, `migrator`), and the
  importable package is its underscored form (`source_service`). Packages are
  workspace-resolved (`{ workspace = true }`) and never published, so no namespacing
  prefix is needed; keep name = folder for clarity. This holds for `common` too —
  its `[project] name` is `common`, matching its folder, with the package at
  `common/common/` (like every service). The virtual workspace root
  (`backend/pyproject.toml`) is the only `pyproject.toml` that declares no package.
- `application/services/` and `application/ports/` are grouped **by domain** (`source/`,
  `scraping/`, `article/`), one subpackage per area with its own `__init__.py` re-exports
  and README; a new area is a new subpackage, never a module at the root of `services/`
  or `ports/`. Callers import from the subpackage.
- Lint from the repo root with `uvx ruff@0.14.0 check backend`.

## Frontend

- `frontend/` is a React SPA (Vite, TypeScript, React Router, `src/`). No SSR —
  `npm run build` emits static files (`dist/`).
- Lint with `npm run lint` (oxlint, config in `.oxlintrc.json`) from `frontend/`.

## CI

- Two workflows, each path-filtered: `.github/workflows/backend.yml` (Ruff on
  `backend/`) and `frontend.yml` (oxlint on `frontend/`). A change touches only
  the relevant job.

## Deployment / networking

- `docker-compose.yml` lives at the repo root and orchestrates all parts.
- **Only nginx publishes a host port (80).** Backend services (`source_service`,
  `news_service`, `npa_service`), `postgres`, and `rabbitmq` are internal-only (`expose`, no host
  `ports`). There is no separate frontend container. The one exception is the local-only
  `docker-compose.dev.yml` overlay, whose `frontend_dev` (Vite HMR) publishes 5173 — it
  never runs on the server.
- The `nginx` image (`nginx/Dockerfile`, build context = repo root) serves the SPA
  (fallback to `index.html`) and gives each backend its own `/api/<service>/`
  namespace — currently **`/api/sources/*` → `source_service:8000`** with the whole
  `/api/sources` prefix stripped, so the OpenAPI spec is reachable at
  `/api/sources/openapi.json` — and **`/api/news/*` → `news_service:8000`**, **`/api/npa/*` → `npa_service:8000`** likewise.
  New services get a sibling `/api/<name>/` location until a full API gateway lands
  (`plans/api-gateway.md`). `/logs/*` → `dozzle:8080` (Dozzle's own login) is the log viewer.
- Backend service images build from `./backend`.
