# news

DTOs for the `News` resource — one class per module, re-exported from `__init__.py`
(import as `from news_service.application.dto.news import NewsOut`).

- `out.py` — `NewsOut`: the response shape (`from_attributes=True`, built from ORM) —
  every `NewsDTO` field plus `id`, `dismissed_at`, `is_alert`, `created_at`.
- `page.py` — `NewsPage`: `{items: NewsOut[], total}` — one page and the count matching
  the same filters, what `GET /` returns.
- `query.py` — `NewsQuery`: what the feed is asked for (`q`, `since`, `visibility` —
  `NewsVisibility.VISIBLE` (default) / `DISMISSED` / `ALL`, `limit`, `offset`) with its bounds (`DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`); FastAPI reads
  it straight off the query string (`Annotated[NewsQuery, Query()]`), the use case and the
  repository take it as one object.

News is written only by the bus consumer (`NewsDTO` from `common`); dismiss / restore take
just the id from the path, and escalation's optional body is the shared
`common.entities.npa.NpaDTO`.

Notes: the module name drops the redundant `news` prefix (enclosing package already
names it) — `create.py`, not `news_create.py`.
