# common.core

Core infrastructure shared by every service: logging and the DB layer.

- `logging.py` — `configure_logging()` + `get_logger()` over stdlib `logging`.
- `base.py` — `Base` (DeclarativeBase) that every ORM model inherits.
- `session.py` — async `engine`, `async_session_factory`, and `get_session`
  (per-request dependency; caller commits/rolls back).

Notes: log via `get_logger` (no `print`). URL comes from `settings.async_database_url`
(asyncpg); Alembic uses the sync URL (psycopg2) — the schema history lives in the
`migrator` service. Settings themselves live in `common/settings.py`.
