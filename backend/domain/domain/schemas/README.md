# schemas

Shared SQLAlchemy ORM models for the **one database** every service uses, one public
class per module (re-exported from `__init__.py`).

- `source.py` — `Source`: ORM model for the `source` table. `id` is a DB-generated
  UUID (`gen_random_uuid()`), not a serial int. `reliability`
  (`domain.entities.source.SourceReliability`) defaults to `medium`.

Notes: `Source` inherits `domain.core.base.Base`. These live in `domain` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`domain.schemas` so `Base.metadata` sees every table.
