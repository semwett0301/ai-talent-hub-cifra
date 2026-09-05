# Repo structure

Backend and frontend are separated; the root holds only deployment and shared
repo files.

```
backend/     all Python — its own uv workspace (root pyproject = virtual workspace root, no package)
  domain/    shared kernel, its own pyproject; package at domain/domain (imported as `domain`)
             core/ (settings/logging/db/errors/rabbit subpackages) + entities/ (business shapes) + schemas/ (shared ORM models)
  source_service/, news_service/, migrator/   one package per service, siblings of domain (no services/ wrapper)
frontend/    React SPA (Vite, TypeScript, React Router) — built to static files
nginx/       edge image: serves static SPA + proxies /api/* → services, /logs/* → dozzle
docker-compose.yml, README, CLAUDE.md, .github, .claude   ← root
```

## Backend

- The backend is a **uv workspace** rooted at `backend/`. `backend/pyproject.toml`
  is a **virtual workspace root** — it declares no package of its own, only
  `[tool.uv.workspace]` members plus the shared dev tooling (ruff/mypy/pytest). Run
  uv from `backend/`.
- One shared kernel only — `backend/domain/`, a regular workspace member with its
  own `pyproject.toml` (package code at `domain/domain/`). Do not add a `libs/`
  wrapper.
- **The DB is one for all services, so ORM schemas are shared.** Every ORM model
  lives in `domain/schemas/` (re-exported from `domain.schemas`), not per service —
  every service and the `migrator` import the same tables. The Alembic history is
  centralized in the `migrator`, which imports `domain.schemas`.
- **`domain` holds:** `core/` (settings, logging, db infra), `entities/` (business
  shapes, grouped by domain — e.g. `entities/news`), and `schemas/` (shared ORM
  models). Service dirs hold only that service's own logic (use cases, ports,
  collectors, routes). **No cross-service imports** — services communicate only
  through `domain` and the message bus, never importing each other; the `migrator`
  imports only `domain.schemas`.
- Each service is a sibling dir of `domain` with its own **uniquely named**
  importable package (e.g. `source_service`, not a generic `app`), `pyproject.toml`
  (depending on `domain`), and `Dockerfile`. New service = copy
  `backend/source_service`, add it to `[tool.uv.workspace] members` in
  `backend/pyproject.toml`, and add a block to `docker-compose.yml`.
- **Project names match the directory — no `cifra-` (or any) prefix.** The
  `[project] name` is the folder name (`source-service`, `migrator`), and the
  importable package is its underscored form (`source_service`). Packages are
  workspace-resolved (`{ workspace = true }`) and never published, so no namespacing
  prefix is needed; keep name = folder for clarity. This holds for `domain` too —
  its `[project] name` is `domain`, matching its folder, with the package at
  `domain/domain/` (like every service). The virtual workspace root
  (`backend/pyproject.toml`) is the only `pyproject.toml` that declares no package.
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
  `ports`). There is no separate frontend container.
- The `nginx` image (`nginx/Dockerfile`, build context = repo root) serves the SPA
  (fallback to `index.html`) and gives each backend its own `/api/<service>/`
  namespace — currently **`/api/sources/*` → `source_service:8000`** with the whole
  `/api/sources` prefix stripped, so the OpenAPI spec is reachable at
  `/api/sources/openapi.json` — and **`/api/news/*` → `news_service:8000`**, **`/api/npa/*` → `npa_service:8000`** likewise.
  New services get a sibling `/api/<name>/` location until a full API gateway lands
  (`plans/api-gateway.md`). `/logs/*` → `dozzle:8080` (Dozzle's own login) is the log viewer.
- Backend service images build from `./backend`.
