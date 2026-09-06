# domain

Pure news-service concepts and rules. The application layer orchestrates them; infrastructure
only persists or evaluates them.

- `dedup/` — per-news event summaries, candidate clusters, membership decisions, and the
  fail-closed assignment policy.
- `ranking/` — company profile, one-cluster targets, explainable results, and pure
  relevance rules.
