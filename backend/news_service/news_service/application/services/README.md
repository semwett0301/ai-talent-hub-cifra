# services

Application services — use cases. Every area is its own subpackage — the root holds
only `__init__.py`/`README.md`, no loose modules.

- `news_ingestor/` — the whole batch ingestion pipeline as one package (`NewsIngestor`
  orchestrator + its `NewsPipelineStage` contract + the `news_deduplicator/`/
  `news_ranker/` stages), grouped like `source_service/application/services/web/`
  groups its crawl stages. See `news_ingestor/README.md`.
- `news_feed/` — `NewsFeed`: the read side over `NewsRepository` — `list(query)` (every
  item matching the filters, newest publication first), `get`,
  `dismiss` / `restore` (stage `dismissed_at` set / cleared, then `commit()`; None and no
  commit for an unknown id, which the API maps to 404). Unrelated to the ingestion
  pipeline — its own subpackage, not a pipeline stage.
- `npa_escalation/` — `NpaEscalation`: `escalate(news_id, NpaDTO | None)` — stage
  `is_alert = true`, `NpaGateway.create` the act (the body, or `_act_from_news` — url /
  title / text / published_at of the item itself), `commit()`. None (nothing sent) for an
  unknown id; a `NpaGatewayError` from the gateway propagates before `commit()`, so the
  request's session closes uncommitted and the flip is rolled back — the item is flagged
  only when `npa_service` confirmed the act. Logs one `news escalated` line. Its own
  subpackage, same reason as `news_feed/`.

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra. The batching itself (timer / size / ack) is **not** here — it is a property
of the broker protocol, so it lives in the shared `common.core.rabbit`; application
only sees "here is a batch".
