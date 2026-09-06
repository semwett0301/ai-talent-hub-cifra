# repositories

Repository implementations of the application repository port — async query helpers
over SQLAlchemy.

- `news_repo.py` — `NewsRepo(session)`: implements the read-API's `NewsRepository` over
  **the one `AsyncSession` it is given** — it opens and closes nothing;
  `deps.get_news_repo` scopes one session per HTTP request. Reads: `list_matching`
  applies `_filters(query)` (`dismissed_at IS NULL` / `IS NOT NULL` / no clause per
  `visibility`, `coalesce(published_at, created_at) >= since`, `ILIKE` on title and text
  with LIKE wildcards escaped by `_like_pattern`), `get`. Writes stage on the session:
  `mark_alert` / `mark_dismissed` (keeps an earlier moment) / `mark_restored` (`flush`, no
  commit). `commit()` commits the session; a driver / connection failure is raised as
  `NewsStoreError`. The consumer's own write path does not go through this class — see
  `dedup_repo.py` / `ranking_repo.py` below.
- `dedup_repo.py` — `SqlDedupRepository`: **opens a fresh session per call** (no shared
  unit of work — the consumer pipeline calls it once per stage, not once per request).
  Checkpoints summaries before embeddings, resumes either stage while the cluster is
  null, retrieves candidates through cosine pgvector search, loads the oldest/newest
  anchors, and writes final assignments. `save_summaries` skips (not detaches) items
  whose source is gone — `source_id` is `NOT NULL`, so an orphan cannot be inserted at
  all — one WARNING per batch naming the dropped ids, not one per item.
- `ranking_repo.py` — `SqlRankingRepository`: same fresh-session-per-call shape; loads
  each affected dedup cluster once using bounded oldest/newest anchors and upserts one
  cluster-level relevance result.

Notes: all three classes explicitly inherit their ports. Sessions come from
`common.core.db`, but only the composition root touches the factory. The upserts use the
**PostgreSQL dialect** `insert` (`sqlalchemy.dialects.postgresql`) — the generic
`sqlalchemy.insert` has no `on_conflict_do_update`/`on_conflict_do_nothing`. The source
check in `dedup_repo.py` is a separate statement rather than a LEFT JOIN folded into the
insert, on purpose: a source deleted between the two only costs one nack + requeue (the
retry no longer sees it), and the FK on `news.source_id` can never sink a whole batch —
`ON CONFLICT` covers unique violations only, not FK ones.
