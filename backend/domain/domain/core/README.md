# domain.core

Base infrastructure shared by every service, one subpackage per concern. Import from
the subpackage (`from domain.core.settings import settings`), not from the modules
inside it.

- `settings/` — `Settings` + the `settings` singleton (pydantic-settings over the
  repo-root `.env`). The only way to read config — never `os.environ`.
- `logging/` — `configure_logging()` / `get_logger()` over stdlib `logging`, with the
  noisy-library caps (`NOISY_LOGGERS`, `CHATTY_LOGGERS`).
- `db/` — the declarative `Base` every ORM model inherits, plus the async `engine`,
  `async_session_factory`, and `get_session`.
- `rabbit/` — the shared RabbitMQ **batch consumer** (`RabbitBatchConsumer[T]`,
  `BatchHandler[T]`, `BatchConsumerConfig`, `BatchStoreError`): a service supplies a
  pydantic message model + a handler, the mechanism (prefetch, buffer, ack-after-store,
  requeue) lives here once.

Notes: `settings` is imported by `logging` and `db`, so it must stay dependency-free
within `core`. Alembic uses `settings.sync_database_url`; everything else the async one.
