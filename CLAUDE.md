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
  domain/                 # shared kernel (one DB → shared schemas), its own pyproject
    domain/               #   importable package: core (settings/logging/db/errors/rabbit), entities, schemas
    pyproject.toml        #   the `domain` package
  source_service/         # project source-service — FastAPI ingestion service
    source_service/       #   importable package (uniquely named, not generic `app`)
    Dockerfile            #   image build (context ./backend)
    pyproject.toml        #   depends on `domain`
  news_service/           # project news-service — RabbitMQ → DB batch consumer + news list/dismiss/escalate-to-NPA
    news_service/         #   importable package; same onion layout as source_service
    Dockerfile, pyproject.toml
  npa_service/            # project npa-service — legislative acts (НПА): list/get/create; called by news_service over HTTP
    npa_service/          #   importable package; same onion layout
    Dockerfile, pyproject.toml
  migrator/               # one-shot Alembic runner — owns the shared DB schema history
    migrations/           #   single Alembic history (all services) + alembic.ini
    Dockerfile, pyproject.toml
  pyproject.toml          # virtual workspace root — members + shared ruff/mypy/pytest (no package)
  uv.lock                 # committed lockfile
frontend/                 # React SPA — Vite + TypeScript + React Router
  src/                    #   main.tsx, App.tsx, pages/, assets/
  public/                 #   static assets served as-is
  .oxlintrc.json          #   linter config
dozzle/                   # log viewer config: users.yml (gitignored login) + README
nginx/                    # edge: serves static SPA + reverse-proxies /api/sources/* → source_service, /api/news/* → news_service, /api/npa/* → npa_service, /logs/* → dozzle (own login)
  Dockerfile              #   multi-stage: node build → nginx serving dist/
  templates/default.conf.template
docker-compose.yml        # root: nginx (public) + migrator + source_service + news_service + npa_service + postgres + rabbitmq + dozzle (internal)
.github/workflows/        # backend.yml (ruff), frontend.yml (oxlint)
.claude/                  # rules/ + skills/ (agent harness)
terraform/                # DigitalOcean infra (Terraform + cloud-init)
.env.example              # THE env template for every part — backend, frontend,
                          #   nginx, compose, terraform, deploy (copy to .env)
README.md, .mcp.json, .gitignore
gen_session.py            # one-off: interactive Telegram login → TELEGRAM_SESSION string
```

`backend/domain` holds the shared kernel — ORM `schemas` (one DB for all), business
`entities`, and `core` infra — and grows with shared LLM code as introduced.
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

- **Only nginx publishes a host port (80).** Backend services (`source_service`,
  `news_service`, `npa_service`), `postgres`, and `rabbitmq` are reachable only on the internal
  compose network (`expose`, no host ports) — everything else stays closed.
- The `nginx` image serves the static React SPA (fallback to `index.html`) and
  gives each backend its own **`/api/<service>/` namespace**. Currently it
  **reverse-proxies `/api/sources/*` → `source_service:8000`** with the whole
  `/api/sources` prefix stripped (so `/api/sources` → `/`,
  `/api/sources/openapi.json` → `/openapi.json`), so the OpenAPI spec is reachable
  at `/api/sources/openapi.json`. `news_service` has the sibling **`/api/news/*` →
  `news_service:8000`** location (`NEWS_API_PREFIX`), `npa_service` has **`/api/npa/*` →
  `npa_service:8000`** (`NPA_API_PREFIX`). `news_service` also calls `npa_service`
  directly over the compose network (`NPA_SERVICE_URL`), not via nginx. New services get their own
  `/api/<name>/` location until a full API gateway lands (`plans/api-gateway.md`).
  **`/logs/*` → `dozzle:8080`** (`LOGS_PREFIX`, prefix kept; Dozzle does its own login
  from the gitignored `dozzle/users.yml`) is the container-log viewer — not an API namespace.
  There is **no separate frontend container**. Edit
  `nginx/templates/default.conf.template` and `nginx/Dockerfile`. Each prefix is a
  single source of truth — `SOURCES_API_PREFIX` / `NEWS_API_PREFIX` in the root
  `.env` — shared with both nginx (envsubst'd into the template) and the service
  (`domain.core.settings.settings.<name>_api_prefix`, used as FastAPI's
  `root_path`); change it there, not in either file directly.

## Architecture rules (backend)

- `domain` is the **shared kernel** — `core` (settings/logging/db infra), `entities`
  (business shapes), and `schemas` (ORM models). The **DB is one for all services**,
  so every ORM model lives in `domain.schemas` (not per service), and the Alembic
  history is centralized in the `migrator`, which imports `domain.schemas`.
- Service-specific logic (use cases, ports, collectors, routes) stays **in that
  service**; only genuinely shared things go in `domain`.
- **No cross-service imports** — services communicate via `domain` (schemas +
  entities) and the message bus, never importing each other. The `migrator` imports
  only `domain.schemas`, not any service.
- Endpoints stay thin; keep LLM and network I/O in services / `domain`. Never
  return ORM objects raw — map through Pydantic schemas/DTOs.

## Conventions

Backend (Python):
- **Async everywhere** on the request path.
- **Config** only through `domain.core.settings.settings` — never read
  `os.environ`; add a field to `Settings`. Every variable in the project (backend,
  frontend, nginx, compose, Terraform, deploy) is declared in the **root
  `.env.example`** and documented in `README.md` — there is no per-folder env file.
- **Logging** via `domain.core.logging.get_logger` (stdlib `logging`). No `print`.
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
uv sync --all-packages            # install domain + all services + dev tools
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
- **New backend service** → create `backend/<name>/` (a sibling of `domain`) with a
  `pyproject.toml` (depend on `domain`), a **uniquely named** importable package
  (`<name>/`, not a generic `app`), and a `Dockerfile`; add `<name>` to
  `[tool.uv.workspace] members` in `backend/pyproject.toml` and a block to
  `docker-compose.yml`.
- **Shared code** (ORM schemas, business entities, DB session, LLM) → add under
  `backend/domain/` (`schemas/`, `entities/`, `core/`) and its deps to
  `domain/pyproject.toml`.
- **Migrations** → live in the `migrator` (`backend/migrator/`), a single shared
  Alembic history. Adding a table = define the model in `domain/schemas/` and
  re-export it from `domain.schemas.__init__`, then autogenerate a revision (`env.py`
  imports `domain.schemas`, so no migrator change is needed). The compose `migrator`
  one-shot runs `upgrade head` before DB-backed services start.
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
  `30-python`, `40-monorepo`, `50-docs`, `60-logging`. Consult the matching one
  before implementing. `50-docs` = keep each folder's `README.md` (file map +
  notes) current when you change files in it. `60-logging` = one INFO line per
  logical action (received / published / registered / …), library noise capped.
