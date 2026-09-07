# services/news_ingestor/news_ranker

The ingestion pipeline's ranking stage.

- `news_ranker.py` — `NewsRanker`: implements `NewsPipelineStage`. Loads each affected
  cluster once, assesses impact and urgency, combines the score with BM25 lexical
  relevance, and persists one explainable result per cluster.
