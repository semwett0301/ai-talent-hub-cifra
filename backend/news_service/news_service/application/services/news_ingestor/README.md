# services/news_ingestor

The batch ingestion pipeline, as one package — root orchestrator plus its stages, like
`source_service/application/services/web/` groups `web_crawl.py` with
`hubs/`/`listings/`/`articles/`.

- `news_ingestor.py` — `NewsIngestor`: the orchestrator. Implements the shared
  `common.core.rabbit.BatchHandler[NewsDTO]` directly, assembled once by
  `deps.build_consumer()`. Checkpoints every per-news summary first (the same write sets
  `news.is_alert` when the extraction flagged a regulatory alert — one `news alert raised`
  line per such item), embeds missing
  vectors, then runs the injected `NewsPipelineStage` stages in order — each stage opens
  its own repository session per call, not one shared session per batch. Retries reuse
  stored summaries instead of calling the LLM again.
- `pipeline_stage.py` — `NewsPipelineStage`: the ordered-stage contract `NewsIngestor`
  runs. Lives here, not in `application/ports/`, because it never crosses into
  infrastructure — both its implementers below and its one consumer (`NewsIngestor`)
  are nested in this same package.
- `news_deduplicator/` — `NewsDeduplicator`: the dedup stage. See
  `news_deduplicator/README.md`.
- `news_ranker/` — `NewsRanker`: the ranking stage. See `news_ranker/README.md`.

Notes: `NewsIngestor` lets `NewsStoreError` / `NewsProcessingError` (both
`BatchStoreError`) propagate so the consumer nacks instead of acknowledging (requeue by
default, see `NEWS_REQUEUE_ON_STORE_ERROR`).
