# migrations

Alembic — the **shared** schema history for all services on the one database
(owned by the `migrator`). See `../README.md` for how it runs.

- `env.py` — sync engine from `settings.sync_database_url`; imports `domain.schemas`
  so every ORM model registers on `Base.metadata`, then runs the migrations.
- `script.py.mako` — revision template.
- `versions/` — the single linear history. `0001_initial_source` creates the `source`
  table; `0002_seed_sources` seeds the starting source list (data migration, inline
  `sa.table` — no model import); `0003_source_uuid_id` switches the surrogate id to a
  DB-generated UUID and shrinks `link` to varchar(255); `0004_source_reliability`
  adds the `reliability` column; `0005_seed_test_source` seeds the `Тест` Telegram
  channel used for manual end-to-end checks.

Notes: run from `../` (the migrator dir) — `uv run alembic -c alembic.ini upgrade head`.
Autogenerate: `uv run alembic -c alembic.ini revision --autogenerate -m "msg"`. Models
come from the shared `domain.schemas`; add a table there and autogenerate a revision.
Data migrations must define tables inline (`sa.table(...)`), never by importing models.
