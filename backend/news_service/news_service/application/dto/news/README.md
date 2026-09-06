# news

DTOs for the `News` resource — one class per module, re-exported from `__init__.py`
(import as `from news_service.application.dto.news import NewsOut`).

- `out.py` — `NewsOut`: the response shape (`from_attributes=True`, built from ORM) —
  the pre-flat-row `NewsDTO` fields (`source_*`, `url`, `text`, `published_at`) plus
  `id`, `is_alert`, `created_at`. Deliberately frozen while the news API is untouched:
  `raw` is gone because the row has none; the new columns (`title`, `excerpt`,
  `updated_at`, `source_name`, `source_tags`) are not exposed yet.

No input DTOs: news is written only by the bus consumer (`NewsDTO` from `common`),
dismiss takes just the id from the path, and escalation's body is the shared
`common.entities.npa.NpaDTO`.

Notes: the module name drops the redundant `news` prefix (enclosing package already
names it) — `create.py`, not `news_create.py`.
