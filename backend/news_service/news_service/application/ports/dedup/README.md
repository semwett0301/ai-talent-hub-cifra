# ports/dedup

Mirrors `infrastructure/dedup/` — one port per implementation there.

- `event_models.py` — `EventModels`: batched extraction/summary (which also yields the
  regulatory-alert verdict, `EventSummary.is_regulatory_alert`) and precluster-alignment
  LLM stages.
- `summary_embedder.py` — `SummaryEmbedder`: async summary-embedding contract (a network
  call in practice, so the pipeline awaits it).
