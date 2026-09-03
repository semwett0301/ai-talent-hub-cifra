# repositories

Repository implementations of the application repository ports — async query helpers
over a SQLAlchemy session.

- `source_repo.py` — `SourceRepo`: implements `SourceRepository` (list / get /
  `list_enabled(type)` + create/update/delete). Mutations commit.

Notes: structurally satisfies the port (no import of it); `deps.py` builds it with a
session and injects it. The session comes from `common.core.session`.
