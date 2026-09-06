# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `npa_repo.py` — current-state reads, active-tracking reads, version history,
  transactional registration/update, and lightweight unchanged checks. It opens a fresh
  session per call and maps the URL unique-key failure to `NpaAlreadyExistsError`.

Notes: `NpaRepo` **inherits** the `NpaRepository` port (explicit conformance) and is
re-exported from `__init__.py`. Sessions come from `common.core.db`.
