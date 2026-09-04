# domain.core

Base infrastructure shared by every service: settings, logging, and the DB layer.

- `settings.py` — `Settings` (pydantic-settings, reads the repo-root `.env`) +
  the `settings` singleton. Read config only through it (never `os.environ`).
- `logging.py` — `configure_logging()` + `get_logger()` over stdlib `logging`;
  caps `NOISY_LOGGERS` (aio_pika/aiormq/pamqp, pyrogram, httpx, urllib3,
  charset_normalizer, newspaper, readability) at INFO so `DEBUG=true` doesn't
  drown business logs in AMQP frames, MTProto updates and extractor DOM scoring;
  `CHATTY_LOGGERS` (newsplease, which announces its pipeline at INFO on every
  article) are capped at WARNING.
- `base.py` — `Base` (DeclarativeBase) that every ORM model inherits.
- `session.py` — async `engine`, `async_session_factory`, and `get_session`
  (per-request dependency; caller commits/rolls back).

Notes: log via `get_logger` (no `print`). URL comes from `settings.async_database_url`
(asyncpg); Alembic uses the sync URL (psycopg2) — the schema history lives in the
`migrator` service.
