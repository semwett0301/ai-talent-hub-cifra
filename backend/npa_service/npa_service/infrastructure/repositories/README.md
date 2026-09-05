# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `npa_repo.py` — `NpaRepo`: implements `NpaRepository` (`list_all(limit, offset)`,
  `get`, `add`). **Opens a fresh session per call** (`async_session_factory`). `add`
  inserts the `NpaDTO` (its `HttpUrl` stored as a plain string) and maps the unique-key
  `IntegrityError` to `NpaAlreadyExistsError`.

Notes: `NpaRepo` **inherits** the `NpaRepository` port (explicit conformance) and is
re-exported from `__init__.py`. Sessions come from `domain.core.db`.
