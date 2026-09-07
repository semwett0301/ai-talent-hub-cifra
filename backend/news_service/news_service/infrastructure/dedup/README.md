# dedup

Outbound implementations for event deduplication — all through OpenRouter, nothing runs
locally.

- `openrouter_event_models.py` — one batched call per news item produces the primary-event
  flag and its summary together; a separate batched call does membership alignment,
  through OpenRouter/LangChain.
- `openrouter_summary_embedder.py` — `OpenRouterSummaryEmbedder`: the OpenRouter
  Embeddings API (`POST /embeddings`, official `openrouter` SDK), `NEWS_DEDUP_EMBEDDING_MODEL`
  per request of up to `NEWS_DEDUP_EMBEDDING_BATCH_SIZE` summaries. Vectors are re-ordered
  by the response `index`, checked against the schema's 1024 dimensions, and L2-normalized
  before they reach pgvector.
- `prompts.py` — precision-first model instructions.
