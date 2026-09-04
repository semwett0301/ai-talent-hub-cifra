# schemas

DB-backed data shapes (SQLAlchemy ORM), one public class per module
(re-exported from `__init__.py`).

- `source.py` — `Source`: SQLAlchemy ORM model for the `source` table (the table this
  service owns; its schema history lives in `../../../migrator`). `id` is a
  DB-generated UUID (`gen_random_uuid()`), not a serial int.

Notes: `Source` imports `common.core.base.Base` and SQLAlchemy. Plain in-memory
shapes (no DB involvement) live in `../entities/` instead. The migrator imports
this package (`source_service.domain.schemas`) to pick up `Source` for autogenerate.
