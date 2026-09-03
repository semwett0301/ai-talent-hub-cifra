# common

Shared library imported as `common`. **Only holds what ≥2 services use** — config,
db infrastructure, the cross-service contract. Single-service code lives in that service.

A regular workspace member: the `pyproject.toml` here declares the `common` package,
whose code lives in the nested `common/` dir (like every service's `<name>/<name>/`).

- `pyproject.toml` — the `common` package + its runtime deps (pydantic, SQLAlchemy,
  asyncpg); services depend on it via `{ workspace = true }`.
- `common/settings.py` — `Settings` (pydantic-settings, reads `.env`) + `settings` singleton.
- `common/core/` — logging + DB infra: declarative `Base`, async engine/session factory
  (`get_session`). Tables themselves live in the owning service.
- `common/enums/` — shared enums (`SourceType`), used by the DTO contract and services.
- `common/dto/` — RabbitMQ message contracts (`NewsDTO`, routing keys) shared by the
  producer and consumers.
- (later) `common/llm/` etc. as ≥2 services need them.

Notes: don't put single-service code here — promote to `common` only when a second
consumer appears. Models live in the owning service (e.g. `source_service/models`).
