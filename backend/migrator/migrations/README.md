# migrations

Alembic — the **shared** schema history for all services on the one database
(owned by the `migrator`). See `../README.md` for how it runs.

- `env.py` — sync engine from `settings.sync_database_url`; imports `common.schemas`
  so every ORM model registers on `Base.metadata`, then runs the migrations.
- `script.py.mako` — revision template.
- `versions/` — the single linear history. `0001_initial_source` creates the `source`
  table; `0002_seed_sources` seeds the starting source list (data migration, inline
  `sa.table` — no model import); `0003_source_uuid_id` switches the surrogate id to a
  DB-generated UUID and shrinks `link` to varchar(255); `0004_source_reliability`
  adds the `reliability` column; `0005_seed_test_source` seeds the `Тест` Telegram
  channel used for manual end-to-end checks; `0006_source_rss_link` adds the
  scraping-only `rss_link` column plus a CHECK constraint keeping it null unless
  `type = rss`, and backfills it for the vedomosti/kommersant/cableman sources
  from `0002_seed_sources` (switching telesputnik to `type = web` instead, since
  it has no known feed); `0007_news_table` creates the `news` table `news_service`
  writes bus messages into, with `url` UNIQUE as the dedupe key; `0008_npa_table`
  creates the `npa` table `npa_service` stores legislative acts in (`url` UNIQUE);
  `0009_source_is_relevant` adds `is_relevant` (default true) plus a CHECK constraint
  keeping a non-relevant source always disabled too (`is_relevant OR NOT is_enabled`);
  `0010_news_source_id` links news back to sources;
  `0013_rss_link_table` moves `source.rss_link` into the one-to-many `rss_link` table
  (FK `ON DELETE CASCADE`, `(source_id, url)` UNIQUE), carrying existing values over, and
  replaces the CHECK with the `rss_link_requires_rss_source` trigger — an `rss_link` row
  is refused unless its source is `type = 'rss'`.
  `0013_npa_tracking_versions` adds current tracking state and immutable text/version
  history with overall and per-article summaries. `7199923ff81c` merges the npa and
  news heads that diverged from `0010`. `0018_news_event_dedup` (on top of that merge)
  enables pgvector and adds the per-news summary, extraction, embedding, cluster id, and
  indexes; `0019_news_cluster_ranking` creates one explainable relevance result per event
  cluster. (Several intermediate revisions between `0010` and `0018` — `0011`, `0012`,
  `0014`-`0017` — are not yet described here; this gap predates the merge.)

Notes: run from `../` (the migrator dir) — `uv run alembic -c alembic.ini upgrade head`.
Autogenerate: `uv run alembic -c alembic.ini revision --autogenerate -m "msg"`. Models
come from the shared `common.schemas`; add a table there and autogenerate a revision.
Data migrations must define tables inline (`sa.table(...)`), never by importing models.
