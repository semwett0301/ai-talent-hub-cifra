# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `source_repo.py` — `SourceRepo`: implements `SourceRepository` (`list_all` / `get`
  / `list_enabled(type)` + create/update/delete). **Opens a fresh session per call**
  (`async_session_factory`), so one repo serves both request handlers and the
  long-lived, concurrent background aggregators. Mutations commit; a `source` passed
  to update/delete is `merge`d into the fresh session first.

Notes: `SourceRepo` **inherits** the `SourceRepository` port (explicit conformance)
and is re-exported from `__init__.py`. Sessions come from `domain.core.session`.
