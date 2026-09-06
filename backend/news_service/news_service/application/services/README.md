# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `news_feed.py` — `NewsFeed`: the read side over `NewsRepository` — `list` (paged,
  newest first) and `dismiss` (flips `is_alert` to true; returns None for an unknown
  id, which the API maps to 404).
- `news_ingestor.py` — `NewsIngestor`: checkpoints every per-news summary first, embeds
  summaries still missing vectors, then passes all pending rows into event deduplication.
  Retries reuse stored summaries instead of calling the LLM again.
- `news_deduplicator.py` — `NewsDeduplicator`: plans pgvector candidates only after the
  full batch is summarized, applies the temporal gate, aligns preclusters in one batched
  LLM stage, and persists fail-closed cluster assignments.
- `npa_escalation.py` — `NpaEscalation`: `escalate(news_id, NpaDTO)` — inside one
  `NewsRepository.begin()` transaction: stage `is_alert = true`, `NpaGateway.create`
  the act, commit. None (nothing sent) for an unknown id; a `NpaGatewayError` from the
  gateway propagates and the staged flip is rolled back, so the alert is dismissed only
  when `npa_service` confirmed the act. Logs one `news escalated` line.

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra. The batching itself (timer / size / ack) is **not** here — it is a property
of the broker protocol, so it lives in the shared `common.core.rabbit`; application
only sees "here is a batch".
