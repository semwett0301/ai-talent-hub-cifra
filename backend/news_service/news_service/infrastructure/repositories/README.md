# repositories

Repository implementations of the application repository port — async query helpers
over SQLAlchemy.

- `news_repo.py` — `NewsRepo(session)`: implements `NewsRepository` over **the one
  `AsyncSession` it is given** — it opens and closes nothing; `deps.get_news_repo` scopes a
  session per HTTP request, `deps.BatchScope` one per consumed batch. Reads: `list_matching`
  applies `_filters(query)` (`dismissed_at IS NULL` / `IS NOT NULL` / no clause per
  `visibility`, `coalesce(published_at, created_at) >= since`, `ILIKE` on title and text
  with LIKE wildcards escaped by `_like_pattern`), `get`. Writes stage on the session:
  `add_many` (`SELECT` the batch's `source_id`s that still exist, skip the items whose
  source is gone — `_drop_orphans`, one WARNING per batch naming the gone ids; `0` when
  nothing is left — then a single `INSERT … ON CONFLICT (url) DO NOTHING`, returns the
  inserted row count), `mark_alert` / `mark_dismissed` (keeps an earlier moment) /
  `mark_restored` (`flush`, no commit). `commit()` commits the session; a driver /
  connection failure in `add_many` or `commit` is raised as `NewsStoreError`.

Notes: `NewsRepo` **inherits** the `NewsRepository` port (explicit conformance) and is
re-exported from `__init__.py`. Sessions come from `common.core.db`, but only the
composition root touches the factory. The `insert` is the **PostgreSQL dialect** one
(`sqlalchemy.dialects.postgresql`) — the generic `sqlalchemy.insert` has no
`on_conflict_do_nothing`. The source check is a separate statement rather than a LEFT
JOIN folded into the insert, on purpose: a source deleted between the two only costs one
nack + requeue (the retry no longer sees it), and the FK on `news.source_id` can never
sink a whole batch — `ON CONFLICT` covers unique violations only, not FK ones.
