# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

AI Analytical Center — an AI intelligence hub that collects, structures, and
summarizes industry news for PR/GR teams (media, regulators, Telegram). Hackathon
MVP. See `README.md` for the product brief.

**Current state: skeleton.** A Python backend with one FastAPI service plus a
thin shared library, a base React SPA, and an nginx edge. Domain code (DB,
models, schemas, LLM), UI, migrations, and tests are added on top as it grows.

## How to navigate this repo

- **Every folder has a small `README.md`** with a file map (what each file does)
  and local notes/conventions. **Read a folder's README before working in it**,
  and **update it in the same change** whenever you add/remove/rename/meaningfully
  change files there (rule `50-docs`). CLAUDE.md is the big picture; folder
  READMEs are the local detail.
- Project rules live in `.claude/rules/` — consult the relevant one before
  implementing (see **Skills & rules** below).

## Repo layout

Backend and frontend are separated; the root holds only deployment and shared
repo files.

```
backend/                  # all Python — a single uv workspace
  common/                 # shared library, imported as `common`
    core/                 #   config (pydantic-settings) + logging (stdlib)
  services/
    api/                  # package cifra-api — FastAPI service
      app/                #   application package (main.py: `/`, `/health`)
      Dockerfile          #   image build (context ./backend)
      pyproject.toml      #   depends on `common`
  pyproject.toml          # workspace root AND the `common` package (+ ruff/mypy/pytest)
  uv.lock                 # committed lockfile
  .env.example            # backend settings template
frontend/                 # React SPA — Vite + TypeScript + React Router
  src/                    #   main.tsx, App.tsx, pages/, assets/
  public/                 #   static assets served as-is
  .env.example            #   VITE_-prefixed (public) config
  .oxlintrc.json          #   linter config
nginx/                    # edge image: builds the SPA + serves it + proxies /api
  Dockerfile              #   multi-stage: node build → nginx serving dist/
  nginx.conf
docker-compose.yml        # root: nginx (public) + api + postgres (internal)
.github/workflows/        # backend.yml (ruff), frontend.yml (oxlint)
.claude/                  # rules/ + skills/ (agent harness)
README.md, .mcp.json, .gitignore
```

`backend/common` grows to hold shared DB/models/schemas/LLM code as introduced.
`data/`, `backend/migrations/`, and test dirs are intentionally absent for now.

## Tech stack

- **Backend**: Python 3.12, FastAPI (async), uv workspace. Postgres + SQLAlchemy
  2.0 (async) + Alembic **when data is added**. LangChain (Claude by default) for
  summarization when the LLM layer lands.
- **Frontend**: React 19 + Vite + TypeScript + React Router. Static build (no
  SSR); oxlint.
- **Edge/infra**: nginx reverse proxy, Docker Compose. No Redis/Celery for now —
  reintroduce only if background work is needed.

## Networking (docker)

- **Only nginx publishes a host port (80).** `api` and `postgres` are reachable
  only on the internal compose network (`expose`, no host ports) — everything
  else stays closed.
- The `nginx` image builds the React SPA and serves it as static files; `/api/`
  is proxied to `api:8000` (single backend → `proxy_pass` directly, no
  `upstream`). There is **no separate frontend container**. Client routes fall
  back to `index.html`. Edit `nginx/nginx.conf` and `nginx/Dockerfile`.

## Architecture rules (backend)

- Shared code (config, and later db, models, schemas, LLM) lives in `common`.
  Service dirs hold only that service's own logic.
- When models are added, they live **only** in `common.models`; one shared
  Postgres, one Alembic history.
- **No cross-service imports** — services share via `common`.
- Endpoints stay thin; keep LLM and network I/O in services / `common`. Never
  return ORM objects raw — map through Pydantic schemas.

## Conventions

Backend (Python):
- **Async everywhere** on the request path.
- **Config** only through `common.core.config.settings` — never read
  `os.environ`; add a field to `Settings`.
- **Logging** via `common.core.logging.get_logger` (stdlib `logging`). No `print`.
- Keep deps minimal — add a package to a `pyproject.toml` only when code imports
  it. Line length 100; lint/format with `ruff` (config in `backend/pyproject.toml`).

Frontend (React):
- Call the backend via **relative `/api/...`** (nginx proxies it), configured via
  `VITE_API_BASE_URL`. Only `VITE_`-prefixed vars reach the browser — **no
  secrets**.
- Routes are declared in `src/App.tsx`; one component per route under `src/pages/`.
- Lint with oxlint (`npm run lint`).

## Commands

Backend uses **uv** — one workspace venv + lockfile under `backend/`.

```bash
# Backend (from backend/)
cd backend
uv sync --all-packages            # install common + all services + dev tools
uv run uvicorn app.main:app --reload --app-dir services/api
uvx ruff@0.14.0 check backend     # lint (CI pins ruff 0.14.0)
uvx ruff@0.14.0 format --check backend

# Frontend (from frontend/)
cd frontend
npm install
npm run dev                       # Vite dev server
npm run build                     # static build → dist/
npm run lint                      # oxlint

# Full stack (from repo root) — reachable at http://localhost/
docker compose up --build
```

## CI

Two path-filtered workflows, so a change runs only the relevant job:
- `.github/workflows/backend.yml` — Ruff lint + format check on `backend/`.
- `.github/workflows/frontend.yml` — oxlint on `frontend/`.

## Git / PR flow

- `main` is **protected** — no direct pushes; changes land via PR.
- Branch (`feat/…`, `fix/…`, `refactor/…`) → commit (Conventional Commits, see
  `.claude/rules/20-git.md`) → PR → merge. Don't commit/push unless asked.

## When adding features

- **Frontend UI** → add pages/components under `frontend/src/`, wire routes in
  `App.tsx`. Talk to the API via `/api/...`.
- **New backend service** → create `backend/services/<name>/` with a
  `pyproject.toml` (depend on `common`), an `app/` package, and a `Dockerfile`;
  add a block to `docker-compose.yml`. The workspace glob (`services/*`) picks it
  up automatically.
- **Shared code** (DB session, models, schemas, LLM) → add under `backend/common/`
  and its deps to `backend/pyproject.toml`.
- **Migrations** → introduce Alembic (`backend/migrations/`) with a single shared
  history once models exist; only one service runs `upgrade head` on startup.
- **Tests** → per-service unit tests, or top-level e2e.
- Whatever you touch, **update the folder's `README.md`** to match.

## Guardrails

- Do not commit `.env`, `*.session`, or API keys.
- Out of scope: production load, extra modalities, infosec.
- Don't call the LLM from tests or CI.
- Prefer editing existing code over adding parallel structures.

## Skills & rules

- **Skills** (`.claude/skills/`): official LangChain skills for the LLM/agent
  stack.
- **Rules** (`.claude/rules/`): `00-conventions`, `10-core`, `20-git`,
  `30-python`, `40-monorepo`, `50-docs`. Consult the matching one before
  implementing. `50-docs` = keep each folder's `README.md` (file map + notes)
  current when you change files in it.
