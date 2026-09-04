# migrations

Alembic — the **shared** schema history for all services on the one database
(owned by the `migrator`). See `../README.md` for how it runs.

- `env.py` — sync engine from `settings.sync_database_url`; runs the migrations.
- `autogenerate.py` — `SERVICE_MODEL_MODULES` + `is_autogenerate` /
  `load_service_models`: imports each service's models **only when `--autogenerate`
  is passed**, so `upgrade` needs no service package.
- `script.py.mako` — revision template.
- `versions/` — the single linear history. `0001_initial_source` creates the `source`
  table (owned by source_service); `0002_seed_sources` seeds the starting source
  list (data migration, inline `sa.table` — no service import).

Notes: run from `../` (the migrator dir) — `uv run alembic -c alembic.ini upgrade head`.
Autogenerate: `uv run alembic -c alembic.ini revision --autogenerate -m "msg"`.
Autogenerate imports models, so run it via uv (workspace installed), never in the
migrator image. Data migrations must define tables inline, never `import
source_service.*`.
