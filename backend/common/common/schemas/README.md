# schemas

Shared SQLAlchemy ORM models for the **one database** every service uses, one public
class per module (re-exported from `__init__.py`).

- `source.py` — `Source`: ORM model for the `source` table. `id` is a DB-generated
  UUID (`gen_random_uuid()`), not a serial int. `reliability`
  (`common.entities.source.SourceReliability`) defaults to `medium`. `normalized_link`
  is `link` folded to one spelling (`source_service.domain.urls.source_identity`) and
  `UNIQUE` — the same address added twice is refused by the DB, which the API maps to a
  409. `rss_link` is
  the discovered feed URL, set only for `type=rss` sources — enforced by a CHECK
  constraint, not the ORM. `poll_interval_seconds` is the pull schedule and must be null for `type=telegram`
  (a push source has none) — a CHECK constraint, not the ORM. `is_relevant` (default
  true) is set false by
  `WebCrawlCollector` when a WEB crawl finds no candidates at all; a CHECK
  constraint enforces `is_relevant OR NOT is_enabled` — a non-relevant source is
  always also disabled, DB-enforced regardless of who writes the row.
- `news.py` — `News`: ORM model for the `news` table, written by `news_service` from
  the bus. Same fields as `common.entities.news.NewsDTO` plus `id`/`created_at`;
  `url` is `UNIQUE` (the dedupe key — a story is stored once), `source_id` is a
  nullable, indexed FK to `source` with `ON DELETE SET NULL` (deleting a source keeps
  its news, detached), `raw` is JSONB, `is_alert` (default false) is the flag the
  dismiss endpoint sets.
- `npa.py` — `Npa`: ORM model for the `npa` table (legislative acts), written by
  `npa_service`. `common.entities.npa.NpaDTO` fields plus `id`/`created_at`; `url` is
  `UNIQUE` (one row per act).
- `types.py` — `SOURCE_TYPE` / `SOURCE_RELIABILITY`: the enum-backed VARCHAR column
  types `Source` and `News` share (a constants-only module, not a class).

Notes: models inherit `common.core.db.Base`. These live in `common` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`common.schemas` so `Base.metadata` sees every table.
