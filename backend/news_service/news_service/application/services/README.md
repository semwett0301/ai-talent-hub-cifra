# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `news_feed.py` — `NewsFeed`: the read side over `NewsRepository` — `list` (paged,
  newest first) and `dismiss` (flips `is_alert` to true; returns None for an unknown
  id, which the API maps to 404).
- `news_ingestor.py` — `NewsIngestor`: the `NewsBatchHandler` implementation the bus
  consumer calls. Writes the batch through `add_many` (one transaction; the DB skips
  duplicate urls, including repeats inside the batch — no dedupe in code), logs one
  `news batch stored` line per batch. Lets `NewsStoreError` propagate so the consumer
  nacks instead of acknowledging (requeue by default, see `NEWS_REQUEUE_ON_STORE_ERROR`).

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra. The batching itself (timer / size / ack) is **not** here — it is a property
of the broker protocol, so it lives in the shared `common.core.rabbit`; application
only sees "here is a batch".
