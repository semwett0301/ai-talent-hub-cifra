# common (package)

The importable shared kernel, `import common`. What it holds and why is in `../README.md`;
this file only maps the subpackages.

- `core/` — infra every service uses: `settings/` (all configuration, grouped),
  `logging/`, `db/`, `errors/`, `rabbit/` (the batch consumer).
- `entities/` — cross-service business shapes, grouped by domain (`news/`, `source/`).
- `schemas/` — the SQLAlchemy ORM models of the one shared database.

Notes: services import from the subpackages (`from common.core.settings import settings`),
never from deep modules; each subpackage re-exports its public API from `__init__.py`.
