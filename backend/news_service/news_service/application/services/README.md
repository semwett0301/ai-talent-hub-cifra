# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `news_feed.py` — `NewsFeed`: the read side over `NewsRepository` — `list(query)` (every
  item matching the filters, newest publication first), `get`,
  `dismiss` / `restore` (stage `dismissed_at` set / cleared, then `commit()`; None and no
  commit for an unknown id, which the API maps to 404).
- `news_ingestor.py` — `NewsIngestor`: the `NewsBatchHandler` implementation the bus
  consumer calls, assembled once by `deps.build_consumer()`. Checkpoints every per-news
  summary first, embeds missing vectors, then runs the injected dedup and ranking stages
  in order — each stage opens its own repository session per call, not one shared session
  per batch. Retries reuse stored summaries instead of calling the LLM again. Lets
  `NewsStoreError` / `NewsProcessingError` (both `BatchStoreError`) propagate so the
  consumer nacks instead of acknowledging (requeue by default, see
  `NEWS_REQUEUE_ON_STORE_ERROR`).
- `news_deduplicator.py` — `NewsDeduplicator`: plans pgvector candidates only after the
  full batch is summarized, applies the temporal gate, aligns preclusters in one batched
  LLM stage, and persists fail-closed cluster assignments.
- `news_ranker.py` — `NewsRanker`: loads each affected cluster once, assesses impact and
  urgency, combines dense/BM25/reranker context, and persists one explainable result per cluster.
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
