# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `news_feed.py` — `NewsFeed`: the read side over `NewsRepository` — `list` (paged,
  newest first) and `dismiss` (flips `is_alert` to true; returns None for an unknown
  id, which the API maps to 404).
- `news_ingestor.py` — `NewsIngestor`: the `NewsBatchHandler` implementation the bus
  consumer calls. Dedupes the batch by `url`, writes it through `add_many` (one
  transaction), logs one `news batch stored` line per batch. Lets `NewsStoreError`
  propagate so the consumer requeues instead of acknowledging.

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra. The batching itself (timer / size / ack) is **not** here — it is a property
of the broker protocol, so it lives in the shared `domain.core.rabbit`; application
only sees "here is a batch".
