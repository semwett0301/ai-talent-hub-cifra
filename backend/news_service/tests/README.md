# tests

Unit tests for staged ingestion, fail-closed event clustering, and cluster-level ranking.
All model, embedding, and persistence collaborators are fakes; tests never call external APIs
or download models.

- `test_news_ingestor.py` — summary checkpoint and ordered dedup/ranking stages.
- `test_news_deduplicator.py` — conservative cluster membership.
- `test_news_ranker.py` — one persisted relevance result per cluster.
- `test_dedup_policy.py` — deterministic event-time and uncertainty gates.
