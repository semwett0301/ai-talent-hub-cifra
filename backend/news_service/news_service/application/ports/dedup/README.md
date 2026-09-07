# ports/dedup

Mirrors `infrastructure/dedup/` — one port per implementation there.

- `event_models.py` — `EventModels`: batched extraction/summary and precluster-alignment
  LLM stages.
- `summary_embedder.py` — `SummaryEmbedder`: async summary-embedding contract (a network
  call in practice, so the pipeline awaits it).
