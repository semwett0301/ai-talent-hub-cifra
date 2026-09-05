# common

The shared package imported as `common` — the **shared kernel** every service builds
on. Because all services run on **one database**, this holds not just cross-service
infra and contracts but the **ORM schemas** too, so every service (and the migrator)
uses the same table definitions.

A regular workspace member: the `pyproject.toml` here declares the `common` package,
whose code lives in the nested `common/` dir (like every service's `<name>/<name>/`).

- `pyproject.toml` — the `common` package + its runtime deps (pydantic, SQLAlchemy,
  asyncpg, aio-pika); services depend on it via `{ workspace = true }`.
- `common/core/` — base infra every service uses, one subpackage per concern:
  `settings/` (pydantic-settings over `.env`), `logging/`, `db/` (declarative `Base`,
  async engine/session factory), `errors/` (domain-wide error types such as
  `BatchStoreError`), `llm/` (`LlmCallBudget` — the per-run cap on LLM calls and on
  how many run at once), `rabbit/` (the shared batch consumer any bus consumer service
  reuses).
- `common/entities/` — business shapes, **grouped by domain** (not by technical kind).
  `entities/news/` holds `NewsDTO`, its `SourceType`, and the routing key — all in
  `dto.py`; `entities/npa/` holds `NpaDTO`, the HTTP contract between `news_service`
  and `npa_service`.
- `common/schemas/` — the SQLAlchemy ORM models for the shared DB (`Source`, `News`,
  `Npa`). One history for all, applied by the `migrator`, which imports `common.schemas`.

Notes: keep this coherent — it's the one place every service shares. New tables go in
`common/schemas/`; new business shapes in `common/entities/`.
