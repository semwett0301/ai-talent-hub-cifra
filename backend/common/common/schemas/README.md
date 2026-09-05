# schemas

Shared SQLAlchemy ORM models for the **one database** every service uses, one public
class per module (re-exported from `__init__.py`).

- `source.py` — `Source`: ORM model for the `source` table. `id` is a DB-generated
  UUID (`gen_random_uuid()`), not a serial int. `reliability`
  (`common.entities.source.SourceReliability`) defaults to `medium`. `rss_link` is
  the discovered feed URL, set only for `type=rss` sources — enforced by a CHECK
  constraint, not the ORM.
- `news.py` — `News`: ORM model for the `news` table, written by `news_service` from
  the bus. Same fields as `common.entities.news.NewsDTO` plus `id`/`created_at`;
  `url` is `UNIQUE` (the dedupe key — a story is stored once), `raw` is JSONB,
  `is_alert` (default false) is the flag the dismiss endpoint sets.
- `types.py` — `SOURCE_TYPE` / `SOURCE_RELIABILITY`: the enum-backed VARCHAR column
  types both models share (a constants-only module, not a class).

Notes: models inherit `common.core.db.Base`. These live in `common` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`common.schemas` so `Base.metadata` sees every table.
