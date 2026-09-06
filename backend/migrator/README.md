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
  `news_service` writes bus messages into, with `url` UNIQUE as the dedupe key;
  `0008_npa_table` creates the `npa` table `npa_service` stores legislative acts in,
  `url` UNIQUE; `0009_source_is_relevant` adds `is_relevant` plus its CHECK constraint;
  `0010_news_source_id` adds the nullable, indexed `news.source_id` FK to `source`
  with `ON DELETE SET NULL`; `0011_source_normalized_link` adds `source.normalized_link`,
  backfills it and makes it UNIQUE — its backfill copies the normalisation rather than
  importing it, so the revision keeps applying the same way);
  `0012_telegram_has_no_schedule` clears `poll_interval_seconds` on telegram rows and
  adds the CHECK keeping it null there; `0013_rss_link_table` moves `source.rss_link`
  into the one-to-many `rss_link` table, guarded by a trigger instead of the CHECK;
  `0014_news_flat_shape` replaces `news.raw` with typed columns (`title`, `excerpt`,
  `updated_at`, `source_name`, `source_tags`), backfilled from `raw` — a
  Telegram row's first sentence and hashtags by SQL regex, copied from the collector —
  re-links orphans by `source_link`, deletes the rest and makes `source_id` NOT NULL with
  ON DELETE CASCADE; its downgrade is lossy; `0015_news_dismissed_at` adds the nullable
  `dismissed_at` column).
- `pyproject.toml` — runtime deps `common` + `alembic` + `psycopg2-binary`. Every
  ORM model comes from `common.schemas` (a runtime dep), so no service package is
  pulled in. `package = false` — a runner, not an importable package.
- `Dockerfile` — multi-stage: uv builds the runtime `.venv`
  (`--package migrator --no-default-groups` → common + Alembic), copied onto a clean
  `python:3.12-slim` with the Alembic config/migrations; `CMD alembic upgrade head`.

Notes: run locally from this dir with the root `.env` exported (`set -a; source ../../.env;
set +a`; the dev compose overlay publishes postgres on the host) — `uv run alembic -c
alembic.ini upgrade head`; autogenerate — `uv run alembic -c alembic.ini revision
--autogenerate -m "msg"`.
Both `upgrade` and `--autogenerate` see the full schema because `env.py` imports
`common.schemas`. **Data migrations must define tables inline (`sa.table(...)`)**,
never by importing ORM models, so old revisions stay pinned to their historical
shape. **Adding a table:** define the model in `common/schemas/`, re-export it from
`common.schemas.__init__`, then autogenerate a revision — no migrator change needed.
