# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `news_repo.py` — `NewsRepo`: implements `NewsRepository` (`list_all(limit, offset)`,
  `mark_alert`, and `add_many`). **Opens a fresh session per call** (`async_session_factory`), so one repo serves both request
  handlers and the long-lived consumer. `add_many` is a single
  `INSERT … ON CONFLICT (url) DO NOTHING` — one round trip, one transaction for the
  whole batch — and returns the inserted row count; a driver/connection failure is
  raised as `NewsStoreError`.

Notes: `NewsRepo` **inherits** the `NewsRepository` port (explicit conformance) and is
re-exported from `__init__.py`. Sessions come from `domain.core.db`. The
`insert` is the **PostgreSQL dialect** one (`sqlalchemy.dialects.postgresql`) — the
generic `sqlalchemy.insert` has no `on_conflict_do_nothing`.
