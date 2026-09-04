# domain

The innermost layer — the service's data shapes and the rules around them. Every
other layer may depend on it; it never imports `application`/`infrastructure`/`api`.

- `entities/` — plain data shapes with no DB involvement: `NewsItem` (the shape
  collectors emit).
- `schemas/` — DB-backed data shapes (SQLAlchemy ORM): `Source` (the table this
  service owns).

Notes: only `schemas/` depends on SQLAlchemy / `common.core.base`. New business
concepts (value objects, domain errors) live under `entities/` unless they're
DB-backed, in which case they go under `schemas/`.
