# migrator

One-shot service that owns the **shared DB schema history**. The database is one
for all services, so migrations live here (not per service): the migrator runs
`alembic upgrade head` and exits; DB-backed services wait for it via compose
`depends_on: condition: service_completed_successfully`.

- `alembic.ini` — Alembic config (`script_location = migrations`; URL injected at
  runtime from `common.settings` in `migrations/env.py`).
- `migrations/env.py` — sync engine from `settings.sync_database_url`; runs the
  migrations. Delegates lazy model loading to `migrations/autogenerate.py`.
- `migrations/autogenerate.py` — `SERVICE_MODEL_MODULES` + `is_autogenerate` /
  `load_service_models`: imports each service's models **only for autogenerate**
  (lazy), so `upgrade` needs no service package.
- `migrations/versions/` — the single linear revision history (`0001_initial_source`
  creates the `source` table; `0002_seed_sources` seeds the starting source list;
  `0003_source_uuid_id` switches the surrogate id from a serial int to a
  DB-generated UUID and shrinks `link` to varchar(255)).
- `pyproject.toml` — runtime deps `common` + `alembic` + `psycopg2-binary`; the
  services whose models autogenerate needs live in the **`autogen` dependency
  group** (currently `source-service`) — installed for local autogenerate,
  excluded from the image. `package = false` — a runner, not an importable package.
- `Dockerfile` — multi-stage: uv builds the runtime `.venv`
  (`--package migrator --no-default-groups` → common + Alembic, no services), copied
  onto a clean `python:3.12-slim` with the Alembic config/migrations; `CMD alembic
  upgrade head`.

Notes: run locally from this dir — `uv run alembic -c alembic.ini upgrade head`;
autogenerate — `uv run alembic -c alembic.ini revision --autogenerate -m "msg"`.
`upgrade` never reads model metadata (it replays version scripts), so the shipped
image is service-free; only autogenerate imports models, and it runs via uv where
the whole workspace is installed. **Data migrations must define tables inline
(`sa.table(...)`), never `import source_service.*`** — the runtime image has no
service. **Adding a service with tables:** add it to the `autogen` group here and
append its models module to `SERVICE_MODEL_MODULES` in `autogenerate.py`. Each service ships
a uniquely named top-level package (e.g. `source_service`), so all coexist. Models
stay owned by their service; only the migration *history* is centralized here.
