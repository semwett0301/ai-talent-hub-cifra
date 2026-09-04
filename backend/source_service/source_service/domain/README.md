# domain

The innermost layer — the service's data shapes and the rules around them. Every
other layer may depend on it; it never imports `application`/`infrastructure`/`api`.

- `schemas/` — the data shapes: `Source` (DB-backed SQLAlchemy ORM, the table this
  service owns) and `NewsItem` (a plain in-memory shape collectors emit). They sit
  together and differ only in whether they hit the DB.

Notes: because DB-backed schemas live here, `domain` may depend on SQLAlchemy /
`common.core.base` (pragmatic — no separate ORM-vs-entity split). New business
concepts (value objects, domain errors) live under `schemas/` or a sibling package.
