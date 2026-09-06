# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `news_feed.py` — `NewsFeed`: the read side over `NewsRepository` — `list(query)` (every
  item matching the filters, newest publication first), `get`,
  `dismiss` / `restore` (stage `dismissed_at` set / cleared, then `commit()`; None and no
  commit for an unknown id, which the API maps to 404).
- `news_ingestor.py` — `NewsIngestor`: the `NewsBatchHandler` implementation the bus
  consumer calls (wrapped per batch by `deps.BatchScope`, which owns the session). Stages
  the batch through `add_many` (the DB skips duplicate urls, including repeats inside the
  batch — no dedupe in code), `commit()`s, logs one `news batch stored` line per batch. Lets `NewsStoreError` propagate so the consumer
  nacks instead of acknowledging (requeue by default, see `NEWS_REQUEUE_ON_STORE_ERROR`).
- `npa_escalation.py` — `NpaEscalation`: `escalate(news_id, NpaDTO | None)` — stage
  `is_alert = true`, `NpaGateway.create` the act (the body, or `_act_from_news` — url /
  title / text / published_at of the item itself), `commit()`. None (nothing sent) for an
  unknown id; a `NpaGatewayError` from the gateway propagates before `commit()`, so the
  request's session closes uncommitted and the flip is rolled back — the item is flagged
  only when `npa_service` confirmed the act. Logs one `news escalated` line.

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra. The batching itself (timer / size / ack) is **not** here — it is a property
of the broker protocol, so it lives in the shared `common.core.rabbit`; application
only sees "here is a batch".
