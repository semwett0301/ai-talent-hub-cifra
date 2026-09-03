# AI Analytical Center (Cifra Hackathon)

An AI-powered intelligence hub that automatically **collects, structures, and
summarizes industry news** in a single interface, with full user control over
sources and content.

Built for PR/GR teams who otherwise spend 3–4 hours a day manually monitoring
media, regulators, and Telegram channels.

## What it does

- **Collect** publications from media (RSS), regulator websites, and Telegram.
- **Summarize** with an LLM: short summary, key entities, category, priority.
- **Dashboard** with filtering and search, linking to the original.
- **User control**: add/edit/delete sources; edit or hide articles; add items
  manually.

## Structure

- `backend/` — Python (uv workspace): `common` shared lib + `source_service`
  (FastAPI) + `migrator` (Alembic), as sibling packages. Services follow **onion
  architecture** (domain → application → infrastructure → api, wired in `deps.py`);
  see `backend/README.md`.
- `frontend/` — React SPA (Vite, TypeScript, React Router).
- `nginx/` — edge: builds the SPA, serves it static, proxies `/api`; the only
  service exposed to the host.
- `docker-compose.yml` — nginx (public) + api + postgres (internal).

## Run

```bash
docker compose up --build -d   # everything, reachable at http://localhost/
```

Local dev: backend `cd backend && uv run uvicorn source_service.main:app --reload --app-dir source_service`;
frontend `cd frontend && npm install && npm run dev`.

### Migrations

The `migrator` service owns the single Alembic history for the shared DB. Compose
runs `alembic upgrade head` once at startup; DB-backed services wait for it.

```bash
cd backend/migrator                                            # run from here
uv run alembic -c alembic.ini upgrade head                     # apply migrations
uv run alembic -c alembic.ini revision --autogenerate -m "msg" # after a model change
```

Autogenerate imports each service's models (listed in `SERVICE_MODEL_MODULES` in
`migrations/autogenerate.py`) to diff against the DB — so run it via `uv` where the whole
workspace is installed, then review the emitted revision. `upgrade` never reads
models, so the shipped migrator image carries no service packages. Adding a
service's first table: add the service to the `autogen` dependency group in
`migrator/pyproject.toml` and append its models module to `SERVICE_MODEL_MODULES`.
Each service ships a uniquely named package (e.g. `source_service`), so all coexist.
See `backend/migrator/README.md`.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`.
Types: `feat`, `fix`, `chore`, `refactor` (also `docs`, `test`, `perf`, `style`).
Branch + PR rather than committing to `main`. Full rules in
`.claude/rules/20-git.md`.

## Out of scope (per the brief)

Production-scale load, additional modalities, and information security.
