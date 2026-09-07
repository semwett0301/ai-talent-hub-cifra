# services/npa_escalation

Escalating a news alert into a legislative act. Unrelated to the ingestion pipeline —
its own subpackage, not a pipeline stage.

- `npa_escalation.py` — `NpaEscalation`: `escalate(news_id, NpaDTO | None)` — stage
  `is_alert = true`, register the act via `NpaGateway`, `commit()` only once the act is
  confirmed.
