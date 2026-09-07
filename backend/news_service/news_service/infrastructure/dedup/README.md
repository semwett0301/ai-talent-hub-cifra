# dedup

Outbound implementations for event deduplication.

- `openrouter_event_models.py` — one batched call per news item produces the primary-event
  flag and its summary together; a separate batched call does membership alignment,
  through OpenRouter/LangChain.
- `sentence_transformer_embedder.py` — normalized CPU embeddings for pgvector retrieval.
- `prompts.py` — precision-first model instructions.
