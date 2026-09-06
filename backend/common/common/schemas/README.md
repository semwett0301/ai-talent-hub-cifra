# schemas

Shared SQLAlchemy ORM models for the **one database** every service uses, one public
class per module (re-exported from `__init__.py`).

- `source.py` — `Source`: ORM model for the `source` table. `id` is a DB-generated
  UUID (`gen_random_uuid()`), not a serial int. `reliability`
  (`common.entities.source.SourceReliability`) defaults to `medium`. `normalized_link`
  is `link` folded to one spelling (`source_service.domain.urls.source_identity`) and
  `UNIQUE` — the same address added twice is refused by the DB, which the API maps to a
  409. `rss_links` is the source's feed URLs (`RssLink` rows, loaded with the row via
  `selectin`, deleted with it). `poll_interval_seconds` is the pull schedule and must be null for `type=telegram`
  (a push source has none) — a CHECK constraint, not the ORM. `is_relevant` (default
  true) is set false by
  `WebCrawlCollector` when a WEB crawl finds no candidates at all; a CHECK
  constraint enforces `is_relevant OR NOT is_enabled` — a non-relevant source is
  always also disabled, DB-enforced regardless of who writes the row.
- `rss_link.py` — `RssLink`: ORM model for the `rss_link` table — one feed URL of an RSS
  source (`source_id` FK, `ON DELETE CASCADE`, `(source_id, url)` UNIQUE). Filled by
  `SourceService` from auto-detection, polled by `RssCollector`. Rows are allowed only
  for `type=rss` sources: a DB trigger (`rss_link_requires_rss_source`, migration
  `0013`) refuses the insert otherwise, regardless of who writes the row.
- `news.py` — `News`: ORM model for the `news` table, written by `news_service` from
  the bus. Same fields as `common.entities.news.NewsDTO` plus `id`/`is_alert`/`created_at`,
  one flat row (no JSON blob): `url` is `UNIQUE` (the dedupe key — a story is stored
  once), `title` is `TEXT NOT NULL` with no length cap (the UI truncates), `source_id` is
  a required, indexed FK to `source` with `ON DELETE CASCADE` (a source's news goes with
  it), `source_name` is the name at collection time, `source_tags` is a `TEXT[]` column
  (no index — tags are shown, never filtered on), `excerpt` / `updated_at` are nullable, `is_alert` (default false) is the flag the dismiss endpoint sets.
- `npa.py` — `Npa`: ORM model for the `npa` table (legislative acts), written by
  `npa_service`. `common.entities.npa.NpaDTO` fields plus `id`/`created_at`; `url` is
  `UNIQUE` (one row per act).
- `types.py` — `SOURCE_TYPE` / `SOURCE_RELIABILITY`: the enum-backed VARCHAR column
  types `Source` and `News` share (a constants-only module, not a class).

Notes: models inherit `common.core.db.Base`. These live in `common` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`common.schemas` so `Base.metadata` sees every table.
