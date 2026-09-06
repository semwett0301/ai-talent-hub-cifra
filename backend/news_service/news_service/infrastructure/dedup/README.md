# dedup

Outbound implementations for event deduplication.

- `openrouter_event_models.py` — batched structured extraction, per-news summary, and
  membership alignment through OpenRouter/LangChain.
- `sentence_transformer_embedder.py` — normalized CPU embeddings for pgvector retrieval.
- `prompts.py` — extraction-grounded, precision-first model instructions.
