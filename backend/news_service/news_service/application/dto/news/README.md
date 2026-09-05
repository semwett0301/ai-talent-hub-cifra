# news

DTOs for the `News` resource — one class per module, re-exported from `__init__.py`
(import as `from news_service.application.dto.news import NewsOut`).

- `out.py` — `NewsOut`: the response shape (`from_attributes=True`, built from ORM) —
  the `NewsDTO` fields plus `id`, `is_alert`, `created_at`.

No input DTOs: news is written only by the bus consumer (`NewsDTO` from `common`), and
dismiss takes just the id from the path.

Notes: the module name drops the redundant `news` prefix (enclosing package already
names it) — `create.py`, not `news_create.py`.
