# news

DTOs for the `News` resource — one class per module, re-exported from `__init__.py`
(import as `from news_service.application.dto.news import NewsOut`).

- `out.py` — `NewsOut`: the response shape (`from_attributes=True`, built from ORM) —
  every `NewsDTO` field plus `id`, `dismissed_at`, `is_alert`, `created_at`, and the
  pipeline's results, null until its stage has reached the item: `summary`,
  `event_cluster_id` (read through `News.event_state`) and `relevance` (read through
  `News.cluster_ranking` — `validation_alias`, so the wire name stays `relevance`).
- `relevance.py` — `NewsRelevanceOut`: the cluster's ranking flattened for the UI — `score`
  (0–100), `category` (`RelevanceCategory`, the AI priority), `member_count` (how many stored
  items report the event), `urgency_basis` / `urgency_reason`, and `impact` (one
  `ImpactReasonOut` per dimension). A before-validator turns the `NewsClusterRanking` row
  into that shape, reading the reasons out of its `details["impact"]`.
- `impact_reason.py` — `ImpactReasonOut`: one scored impact dimension (`finance` /
  `reputation` / `technology` / `competition`, 0–3) with the model's grounding.
- `query.py` — `NewsQuery`: what the feed is asked for (`q`, `since`, `visibility` —
  `NewsVisibility.VISIBLE` (default) / `DISMISSED` / `ALL`, `is_alert` — unset shows both,
  `true`/`false` narrows to escalated / not-escalated items); FastAPI reads it straight off
  the query string (`Annotated[NewsQuery, Query()]`), the use case and the repository take
  it as one object. No paging: `GET /` answers every match as a plain `NewsOut[]`.

News is written only by the bus consumer (`NewsDTO` from `common`); dismiss / restore take
just the id from the path, and escalation's optional body is the shared
`common.entities.npa.NpaDTO`.

Notes: the module name drops the redundant `news` prefix (enclosing package already
names it) — `create.py`, not `news_create.py`.
