# schemas

SQLAlchemy ORM models (tables) **owned by this service**. Re-exported from
`__init__.py`. Used directly across layers as the `Source` type (no separate domain
entity).

- `source.py` — `Source`: a configured news source (`type`, `name`, `link`,
  `poll_interval_seconds`, `is_enabled`, timestamps).

Notes: inherit `common.core.base.Base`. The migration history for these tables lives
in the `migrator` service, not here — the migrator imports this module to build the
schema.
