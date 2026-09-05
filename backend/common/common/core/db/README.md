# common.core.db

- `base.py` — `Base` (SQLAlchemy `DeclarativeBase`) that every ORM model in
  `common.schemas` inherits; the migrator reads `Base.metadata` for autogenerate.
- `session.py` — async `engine` (`settings.async_database_url`, `pool_pre_ping`),
  `async_session_factory` (`expire_on_commit=False`), and `get_session` (a session
  per unit of work; the caller commits/rolls back).
- `__init__.py` — re-exports all four.

Notes: repositories open a fresh session per call via `async_session_factory`, so one
repo instance can serve request handlers and a long-lived consumer concurrently.
Alembic uses the sync URL (psycopg2) from `settings`, not this engine.
