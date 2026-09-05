# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `news_repo.py` — `NewsRepo`: implements `NewsRepository` (`list_all(limit, offset)`,
  `mark_alert`, and `add_many`). **Opens a fresh session per call** (`async_session_factory`), so one repo serves both request
  handlers and the long-lived consumer. `add_many` is a single
  `INSERT … ON CONFLICT (url) DO NOTHING` — one round trip, one transaction for the
  whole batch — and returns the inserted row count; a driver/connection failure is
  raised as `NewsStoreError`. `begin()` returns a `SqlNewsTransaction`; `mark_alert`
  is implemented on top of it (stage + commit).
- `news_transaction.py` — `SqlNewsTransaction`: implements `NewsTransaction` over one
  `AsyncSession` it owns — `mark_alert` flushes without committing, `commit()` commits,
  `__aexit__` rolls back whatever is still pending (a no-op after a commit) and closes
  the session. The row stays locked by the `UPDATE` until then, so keep the block short.

Notes: `NewsRepo` **inherits** the `NewsRepository` port (explicit conformance) and both
classes are re-exported from `__init__.py`. Sessions come from `domain.core.db`. The
`insert` is the **PostgreSQL dialect** one (`sqlalchemy.dialects.postgresql`) — the
generic `sqlalchemy.insert` has no `on_conflict_do_nothing`.
