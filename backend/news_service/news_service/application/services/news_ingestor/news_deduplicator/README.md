# services/news_ingestor/news_deduplicator

The ingestion pipeline's dedup stage.

- `news_deduplicator.py` — `NewsDeduplicator`: implements `NewsPipelineStage`. Plans
  pgvector candidates only after the full batch is summarized, aligns preclusters in
  one batched LLM stage, and persists fail-closed cluster assignments.
