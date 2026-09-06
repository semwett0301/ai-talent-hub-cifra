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
  (no index — tags are shown, never filtered on), `excerpt` / `updated_at` are nullable.
  `summary`, `event_extraction`, the 1024-dimensional `summary_embedding`, and
  `event_cluster_id` persist the staged event-dedup pipeline (`news_service.application
  .services.news_deduplicator`); `summary_embedding` has an HNSW cosine index. Two
  service-owned fields: `dismissed_at` (a reader hid the item from the feed) and
  `is_alert` (default false; set when the item is escalated into a legislative act).
- `news_cluster_ranking.py` — one explainable relevance result per deduplicated
  `event_cluster_id`; reranking an affected cluster updates this row rather than
  duplicating the score on every member news item.
- `npa.py` — `Npa`: current State Duma bill snapshot and tracking state; `url` is
  `UNIQUE` (one row per act).
- `npa_version.py` — `NpaVersion`: immutable stage/text snapshots with the plain-language
  overall and per-article change summaries for each transition.
- `types.py` — `SOURCE_TYPE` / `SOURCE_RELIABILITY`: the enum-backed VARCHAR column
  types `Source` and `News` share (a constants-only module, not a class).

Notes: models inherit `common.core.db.Base`. These live in `common` (not a
service) because the DB is shared — every service and the `migrator` import the same
models. The schema history is applied by `../../../migrator`, whose Alembic env imports
`common.schemas` so `Base.metadata` sees every table.
