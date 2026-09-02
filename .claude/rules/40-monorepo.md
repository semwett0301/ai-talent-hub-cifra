# Repo structure

Backend and frontend are separated; the root holds only deployment and shared
repo files.

```
backend/     all Python — its own uv workspace (root pyproject = the `common` package)
  common/    shared package (imported as `common`)
  services/  one package per service (e.g. services/api)
frontend/    React SPA (Vite, TypeScript, React Router) — built to static files
nginx/       edge image: builds the SPA + serves it static + proxies /api
docker-compose.yml, README, CLAUDE.md, .github, .claude   ← root
```

## Backend

- The backend is a **uv workspace** rooted at `backend/`. `backend/pyproject.toml`
  is both the workspace root and the shared `common` package. Run uv from
  `backend/`.
- One shared library only — `backend/common/`. Do not add a `libs/` wrapper.
- **Models live only in `common.models`.** Services never define tables.
- Shared code (config, db, schemas, LLM) goes in `common`; service dirs hold only
  that service's logic. **No cross-service imports** — share via `common`.
- Each service has its own `app` package, `pyproject.toml` (depending on
  `common`), and `Dockerfile`. New service = copy `backend/services/api` and add a
  block to `docker-compose.yml`.
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
- **Only nginx publishes a host port (80).** `api` and `postgres` are
  internal-only (`expose`, no host `ports`). There is no separate frontend
  container.
- The `nginx` image (`nginx/Dockerfile`, build context = repo root) builds the
  SPA and serves it static; `nginx/nginx.conf` proxies `/api/` to `api:8000` and
  falls back to `index.html` for client-side routes.
- The `api` image builds from `./backend`.
