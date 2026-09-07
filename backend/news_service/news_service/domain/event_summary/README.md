# domain/event_summary

The `EventSummary` aggregate: one news item's event understanding. The root holds only the
entity; everything it is made of during ingestion is in `model/`.

- `event_summary.py` — `EventSummary`: persisted text, `has_primary_event` flag, embedding,
  `published_at`. Immutable — `with_embedding(...)` returns a copy one stage further.
- `model/` — the ingestion-stage values `EventSummary` is built from: `NewsTarget`,
  `PreparedNews`, `StoredNewsState`. See `model/README.md`.
