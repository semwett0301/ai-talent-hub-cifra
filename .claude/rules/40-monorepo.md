# Repo structure

Backend and frontend are separated; the root holds only deployment and shared
repo files.

```
backend/     all Python — its own uv workspace (root pyproject = virtual workspace root, no package)
  common/    shared library, its own pyproject; package at common/common (imported as `common`)
  source_service/, migrator/   one package per service, siblings of common (no services/ wrapper)
frontend/    React SPA (Vite, TypeScript, React Router) — built to static files
nginx/       edge image: serves static SPA + proxies /api/* → source_service
docker-compose.yml, README, CLAUDE.md, .github, .claude   ← root
```

## Backend

- The backend is a **uv workspace** rooted at `backend/`. `backend/pyproject.toml`
  is a **virtual workspace root** — it declares no package of its own, only
  `[tool.uv.workspace]` members plus the shared dev tooling (ruff/mypy/pytest). Run
  uv from `backend/`.
- One shared library only — `backend/common/`, a regular workspace member with its
  own `pyproject.toml` (package code at `common/common/`). Do not add a `libs/`
  wrapper.
- **`common` holds only what ≥2 services use.** If something is used by a single
  service, it lives **in that service**; promote it to `common` only when a second
  consumer appears. This applies to everything (models, schemas, helpers).
- **Models live in the owning service.** A model moves to `common.models` only once
  ≥2 services share the table. The DB is one for all services, so the **Alembic
  history is centralized in the `migrator` service** — not per service.
- Shared-by-≥2 code (config, db infra, event/message contracts, LLM) goes in
  `common`; service dirs hold that service's own logic. **No cross-service
  imports** — services communicate only through `common` (contracts) and the
  message bus, never importing each other. The one exception is `migrator`, which
  imports every service's models to build the full schema.
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
- **Only nginx publishes a host port (80).** Backend services (`source_service`),
  `postgres`, and `rabbitmq` are internal-only (`expose`, no host `ports`). There
  is no separate frontend container.
- The `nginx` image (`nginx/Dockerfile`, build context = repo root) serves the SPA
  (fallback to `index.html`) and **reverse-proxies `/api/*` →
  `source_service:8000`** (the `/api` prefix is stripped). Other services stay
  internal until a full API gateway lands (`plans/api-gateway.md`).
- Backend service images build from `./backend`.
