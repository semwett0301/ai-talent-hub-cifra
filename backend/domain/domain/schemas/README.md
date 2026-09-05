# schemas

Shared SQLAlchemy ORM models for the **one database** every service uses, one public
class per module (re-exported from `__init__.py`).

- `source.py` — `Source`: ORM model for the `source` table. `id` is a DB-generated
  UUID (`gen_random_uuid()`), not a serial int. `reliability`
  (`domain.entities.source.SourceReliability`) defaults to `medium`. `rss_link` is
  the discovered feed URL, set only for `type=rss` sources — enforced by a CHECK
  constraint, not the ORM.
- `news.py` — `News`: ORM model for the `news` table, written by `news_service` from
  the bus. Same fields as `domain.entities.news.NewsDTO` plus `id`/`created_at`;
  `url` is `UNIQUE` (the dedupe key — a story is stored once), `raw` is JSONB,
  `is_alert` (default false) is the flag the dismiss endpoint sets.
- `npa.py` — `Npa`: ORM model for the `npa` table (legislative acts), written by
  `npa_service`. `domain.entities.npa.NpaDTO` fields plus `id`/`created_at`; `url` is
  `UNIQUE` (one row per act).
- `types.py` — `SOURCE_TYPE` / `SOURCE_RELIABILITY`: the enum-backed VARCHAR column
  types `Source` and `News` share (a constants-only module, not a class).

Notes: models inherit `domain.core.db.Base`. These live in `domain` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`domain.schemas` so `Base.metadata` sees every table.
