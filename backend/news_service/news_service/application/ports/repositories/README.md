# ports/repositories

Mirrors `infrastructure/repositories/` — one port per implementation there.

- `news_repository.py` — `NewsRepository`: data access over **one unit of work** (one
  HTTP request — scoped by `deps.py`, never by the use case). Reads: `list_matching(query)`
  (every row a `NewsQuery`'s filters admit, newest publication first), `get(id)`. Writes
  *stage* and return the row (None when the id is unknown): `mark_alert(id)`,
  `mark_dismissed(id)`, `mark_restored(id)`. `commit()` persists everything staged; a
  unit of work that ends without it rolls back. `commit()` raises `NewsStoreError` on a
  DB failure. The consumer's own write path — checkpointed ingestion, dedup, ranking —
  goes through `DedupRepository` / `RankingRepository` instead, not this port.
- `dedup_repository.py` — idempotent summarized-news writes, pending work, pgvector
  candidates, and final cluster assignments.
- `ranking_repository.py` — affected-cluster loading and ranking upsert boundary.
