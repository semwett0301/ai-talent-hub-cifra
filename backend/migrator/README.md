# migrator

One-shot service that owns the **shared DB schema history**. The database is one
for all services, so migrations live here (not per service): the migrator runs
`alembic upgrade head` and exits; DB-backed services wait for it via compose
`depends_on: condition: service_completed_successfully`.

- `alembic.ini` — Alembic config (`script_location = migrations`; URL injected at
  runtime from `common.core.settings` in `migrations/env.py`).
- `migrations/env.py` — sync engine from `settings.sync_database_url`; imports
  `common.schemas` so every ORM model registers on `Base.metadata`, then runs the
  migrations.
- `migrations/versions/` — the single linear revision history (`0001_initial_source`
  creates the `source` table; `0002_seed_sources` seeds the starting source list;
  `0003_source_uuid_id` switches the surrogate id from a serial int to a
  DB-generated UUID and shrinks `link` to varchar(255); `0004_source_reliability`
  adds the `reliability` column, defaulting existing rows to `medium`;
  `0005_seed_test_source` seeds the `Тест` Telegram channel used for manual
  end-to-end checks; `0006_source_rss_link` adds the `rss_link` column with its
  `type = rss` CHECK constraint; `0007_news_table` creates the `news` table
  `news_service` writes bus messages into, with `url` UNIQUE as the dedupe key).
- `pyproject.toml` — runtime deps `common` + `alembic` + `psycopg2-binary`. Every
  ORM model comes from `common.schemas` (a runtime dep), so no service package is
  pulled in. `package = false` — a runner, not an importable package.
- `Dockerfile` — multi-stage: uv builds the runtime `.venv`
  (`--package migrator --no-default-groups` → common + Alembic), copied onto a clean
  `python:3.12-slim` with the Alembic config/migrations; `CMD alembic upgrade head`.

Notes: run locally from this dir — `uv run alembic -c alembic.ini upgrade head`;
autogenerate — `uv run alembic -c alembic.ini revision --autogenerate -m "msg"`.
Both `upgrade` and `--autogenerate` see the full schema because `env.py` imports
`common.schemas`. **Data migrations must define tables inline (`sa.table(...)`)**,
never by importing ORM models, so old revisions stay pinned to their historical
shape. **Adding a table:** define the model in `common/schemas/`, re-export it from
`common.schemas.__init__`, then autogenerate a revision — no migrator change needed.
