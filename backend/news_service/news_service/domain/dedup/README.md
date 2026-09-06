# dedup

Domain values for same-event deduplication.

- `event_summary.py` — one persisted, embedded event summary per news row.
- `news_target.py` / `prepared_news.py` / `stored_news_state.py` — ingestion-stage values.
- `candidate_query.py` / `candidate_cluster.py` / `precluster.py` — pgvector retrieval and
  verifier inputs.
- `membership_decision.py` / `cluster_assignment.py` — verifier output and persisted result.
- `policy.py` — temporal gate and fail-closed decision combination.
