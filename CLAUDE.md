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
  common/                 # shared kernel (one DB → shared schemas), its own pyproject
    common/               #   importable package: core (settings/logging/db/errors/llm/rabbit), entities, schemas
    pyproject.toml        #   the `common` package
  source_service/         # project source-service — FastAPI ingestion service
    source_service/       #   importable package (uniquely named, not generic `app`)
    Dockerfile            #   image build (context ./backend)
    pyproject.toml        #   depends on `common`
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

`backend/common` holds the shared kernel — ORM `schemas` (one DB for all), business
`entities`, and `core` infra, including `core/llm` (`LlmCallBudget`: how many LLM calls
one run may make and how many at once — reuse it, don't hand-roll a semaphore).
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
  (`common.core.settings.settings.<name>_api_prefix`, used as FastAPI's
  `root_path`); change it there, not in either file directly.

## Architecture rules (backend)

- `common` is the **shared kernel** — `core` (settings/logging/db/llm infra), `entities`
  (business shapes), and `schemas` (ORM models). The **DB is one for all services**,
  so every ORM model lives in `common.schemas` (not per service), and the Alembic
  history is centralized in the `migrator`, which imports `common.schemas`.
- Service-specific logic (use cases, ports, collectors, routes) stays **in that
  service**; only genuinely shared things go in `common`. A service's own entities and
  pure rules live in its `domain/` layer — entity at the root of its subpackage, `model/`
  for what it is made of, `rules/` for what judges it (rule `80-domain`).
- **No cross-service imports** — services communicate via `common` (schemas +
  entities) and the message bus, never importing each other. The `migrator` imports
  only `common.schemas`, not any service.
- Endpoints stay thin; keep LLM and network I/O in services / `common`. Never
  return ORM objects raw — map through Pydantic schemas/DTOs.

## Conventions

Backend (Python):
- **Async everywhere** on the request path.
- **Config** only through `common.core.settings.settings` — never read
  `os.environ`. Settings are grouped: add a field to the matching template in
  `common/core/settings/templates/` (or a new template + a field on `Settings`), read it
  as `settings.<group>.<field>` (rule `70-settings`). Every variable in the project (backend,
  frontend, nginx, compose, Terraform, deploy) is declared in the **root
  `.env.example`** and documented in `README.md` — there is no per-folder env file.
- **Logging** via `common.core.logging.get_logger` (stdlib `logging`). No `print`.
- Keep deps minimal — add a package to a `pyproject.toml` only when code imports
  it. Line length 100; lint/format with `ruff` (config in `backend/pyproject.toml`).

Frontend (React):
- Call the backend via **relative `/api/...`** (nginx proxies it), using the
  `__SOURCES_API_PREFIX__` / `__NEWS_API_PREFIX__` / `__NPA_API_PREFIX__` constants that
  `vite.config.ts` bakes in from the root `.env` — the same variables nginx and the
  services read, never a second copy. Nothing else from the environment reaches the
  browser — **no secrets**.
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
- `.github/workflows/backend.yml` — Ruff lint + format check, mypy, and pytest on `backend/`.
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
  (`<name>/`, not a generic `app`), and a `Dockerfile`; add `<name>` to
  `[tool.uv.workspace] members` in `backend/pyproject.toml` and a block to
  `docker-compose.yml`.
- **Shared code** (ORM schemas, business entities, DB session, LLM mechanics) → add
  under `backend/common/` (`schemas/`, `entities/`, `core/`) and its deps to
  `common/pyproject.toml`. Anything bounding LLM traffic goes in `core/llm/`.
- **Migrations** → live in the `migrator` (`backend/migrator/`), a single shared
  Alembic history. Adding a table = define the model in `common/schemas/` and
  re-export it from `common.schemas.__init__`, then autogenerate a revision (`env.py`
  imports `common.schemas`, so no migrator change is needed). The compose `migrator`
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
  `30-python`, `40-monorepo`, `50-docs`, `60-logging`, `70-settings`, `80-domain`. Consult the matching one
  before implementing. `50-docs` = keep each folder's `README.md` (file map +
  notes) current when you change files in it. `60-logging` = one INFO line per
  logical action (received / published / registered / …), library noise capped.
