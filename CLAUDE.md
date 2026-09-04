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
backend/                  # all Python — a single uv workspace (services are siblings)
  common/                 # shared library (≥2 services), its own pyproject
    common/               #   importable package: settings, core (logging + db infra), enums, dto
    pyproject.toml        #   the `common` package
  source_service/         # project source-service — FastAPI ingestion service
    source_service/       #   importable package (uniquely named, not generic `app`)
    Dockerfile            #   image build (context ./backend)
    pyproject.toml        #   depends on `common`
  migrator/               # one-shot Alembic runner — owns the shared DB schema history
    migrations/           #   single Alembic history (all services) + alembic.ini
    Dockerfile, pyproject.toml
  pyproject.toml          # virtual workspace root — members + shared ruff/mypy/pytest (no package)
  uv.lock                 # committed lockfile
  .env.example            # backend settings template
frontend/                 # React SPA — Vite + TypeScript + React Router
  src/                    #   main.tsx, App.tsx, pages/, assets/
  public/                 #   static assets served as-is
  .env.example            #   VITE_-prefixed (public) config
  .oxlintrc.json          #   linter config
nginx/                    # edge: serves static SPA + reverse-proxies /api/sources/* → source_service
  Dockerfile              #   multi-stage: node build → nginx serving dist/
  templates/default.conf.template
docker-compose.yml        # root: nginx (public) + migrator + source_service + postgres + rabbitmq (internal)
.github/workflows/        # backend.yml (ruff), frontend.yml (oxlint)
.claude/                  # rules/ + skills/ (agent harness)
README.md, .mcp.json, .gitignore
```

`backend/common` grows to hold shared DB/models/schemas/LLM code as introduced.
`data/` and test dirs are intentionally absent for now.

## Tech stack

- **Backend**: Python 3.12, FastAPI (async), uv workspace. Postgres + SQLAlchemy
  2.0 (async) + Alembic **when data is added**. LangChain (Claude by default) for
  summarization when the LLM layer lands.
- **Frontend**: React 19 + Vite + TypeScript + React Router. Static build (no
  SSR); oxlint.
- **Edge/infra**: nginx reverse proxy, Docker Compose. No Redis/Celery for now —
  reintroduce only if background work is needed.

## Networking (docker)

- **Only nginx publishes a host port (80).** Backend services (`source_service`),
  `postgres`, and `rabbitmq` are reachable only on the internal compose network
  (`expose`, no host ports) — everything else stays closed.
- The `nginx` image serves the static React SPA (fallback to `index.html`) and
  gives each backend its own **`/api/<service>/` namespace**. Currently it
  **reverse-proxies `/api/sources/*` → `source_service:8000`** with the whole
  `/api/sources` prefix stripped (so `/api/sources` → `/`,
  `/api/sources/openapi.json` → `/openapi.json`), so the OpenAPI spec is reachable
  at `/api/sources/openapi.json`. New services get a sibling
  `/api/<name>/` location until a full API gateway lands (`plans/api-gateway.md`).
  There is **no separate frontend container**. Edit
  `nginx/templates/default.conf.template` and `nginx/Dockerfile`. The `/api/sources`
  prefix itself is a single source of truth — the `x-sources-api-prefix` anchor in
  `docker-compose.yml` — shared as `SOURCES_API_PREFIX` with both nginx (envsubst'd
  into the template) and `source_service` (`common.settings.settings.sources_api_prefix`,
  used as FastAPI's `root_path`); change it there, not in either file directly.

## Architecture rules (backend)

- `common` holds **only what ≥2 services use** (config, db infra, event/message
  contracts, LLM). Anything used by a single service lives **in that service**;
  promote to `common` when a second consumer appears.
- Models live in the **owning service**. A model moves to `common.models` only once
  ≥2 services share the table. The DB is one for all services, so the **Alembic
  history is centralized in the `migrator` service** (not per service).
- **No cross-service imports** — services communicate via `common` (contracts) and
  the message bus, never importing each other. The one exception is `migrator`,
  which imports each service's models to build the full schema.
- Endpoints stay thin; keep LLM and network I/O in services / `common`. Never
  return ORM objects raw — map through Pydantic schemas.

## Conventions

Backend (Python):
- **Async everywhere** on the request path.
- **Config** only through `common.settings.settings` — never read
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
uv run uvicorn source_service.main:app --reload --app-dir source_service
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
- **New backend service** → create `backend/<name>/` (a sibling of `common`) with a
  `pyproject.toml` (depend on `common`), a **uniquely named** importable package
  (`<name>/`, not a generic `app` — so services coexist when the migrator imports
  their models), and a `Dockerfile`; add `<name>` to `[tool.uv.workspace] members`
  in `backend/pyproject.toml` and a block to `docker-compose.yml`.
- **Shared code** (DB session, models, schemas, LLM) → add under `backend/common/`
  and its deps to `backend/pyproject.toml`.
- **Migrations** → live in the `migrator` service (`backend/migrator/`), a single
  shared Alembic history. Adding a table = add the service to the `autogen` group
  in `migrator/pyproject.toml` and append its models module to
  `SERVICE_MODEL_MODULES` in `migrations/autogenerate.py`, then autogenerate a
  revision. The
  compose `migrator` one-shot runs `upgrade head` before DB-backed services start.
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
