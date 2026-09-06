# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `news_repo.py` — `NewsRepo`: implements read-side `NewsRepository` (`list_all`,
  `mark_alert`, and `begin()`). **Opens a fresh session per call**. `begin()` returns a
  `SqlNewsTransaction`; `mark_alert`
  is implemented on top of it (stage + commit).
- `dedup_repo.py` — `SqlDedupRepository`: checkpoints summaries before embeddings,
  resumes either stage while the cluster is null, retrieves candidates through cosine
  pgvector search, loads the oldest/newest anchors, and writes final assignments.
- `ranking_repo.py` — `SqlRankingRepository`: loads each affected dedup cluster once
  using bounded oldest/newest anchors and upserts one cluster-level relevance result.
- `news_transaction.py` — `SqlNewsTransaction`: implements `NewsTransaction` over one
  `AsyncSession` it owns — `mark_alert` flushes without committing, `commit()` commits,
  `__aexit__` rolls back whatever is still pending (a no-op after a commit) and closes
  the session. The row stays locked by the `UPDATE` until then, so keep the block short.

Notes: both classes explicitly inherit their ports and open sessions from
`common.core.db`. A missing source is detached before the summarized-news upsert, so a
deleted source cannot sink the whole Rabbit batch.
