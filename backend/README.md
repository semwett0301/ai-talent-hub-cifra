# backend

All Python code, as one uv workspace. The workspace root is virtual (declares no
package); the shared library and each deployable service are sibling member
directories (no `services/` wrapper).

- `common/` — shared library member (its own `pyproject.toml`; package at
  `common/common/`, imported as `common`): `settings`, `core/` = logging + DB infra,
  `enums`, `dto` contracts. Only holds what ≥2 services use.
- `source_service/` — ingestion service: CRUD sources, collect news (stub
  collectors), publish to RabbitMQ. See `../plans/source-service-architecture.md`.
- `migrator/` — one-shot Alembic runner that owns the shared DB schema history (one
  database for all services). Runs `upgrade head` on boot, then exits.
- `pyproject.toml` — virtual workspace root: `[tool.uv.workspace] members` (common +
  the services) + shared dev tooling (ruff/mypy/pytest). No package of its own.
- `uv.lock` — locked versions (committed).
- Settings come from the **repo-root `.env`** (see `../.env.example`); `common.settings`
  loads it by absolute path, so `uv run` works from any directory.

## Service architecture — onion / clean layers

Each service is structured as **onion architecture**: dependencies point **inward**,
toward the domain. Outer layers depend on inner ones, never the reverse; the
concrete wiring happens once, at the composition root.

| Layer | Holds | Depends on |
|-------|-------|-----------|
| `domain/` | Data **schemas** — the DB-backed ORM (`Source`) and plain in-memory shapes (`NewsItem`) — plus business rules. | SQLAlchemy (for the ORM) |
| `application/` | Use cases / orchestration, the **ports** (interfaces) infra implements, and DTOs. | domain |
| `infrastructure/` | Implementations of the ports: repositories, RabbitMQ, collectors (feedparser / Playwright / aiogram), external APIs. | application, domain |
| `api/` | FastAPI routes / controllers and HTTP-only types. | application |
| `deps.py` | **Composition root** — builds the concrete implementations and injects them into application (registries, repository, publisher). | everything |

Inversion in practice: application defines a `Protocol` port (`SourceRepository`,
`NewsPublisher`, `PullCollector`/`PushCollector`); infrastructure supplies a class
that **implements** it (inherits the port); `deps.py` constructs the impl and passes
it in. Application never imports a concrete infra class — only its own ports.
(Pragmatic concession: DB-backed schemas live in `domain/schemas/` next to the plain
ones, so the ports type against the ORM `Source` directly.)

`source_service/` folder layout:

```
source_service/                 # the importable package
  domain/
    schemas/                    # Source (ORM table) + NewsItem (plain shape)
  application/
    ports/                      # collectors.py, repositories.py, publisher.py (Protocols)
    dto/source/                 # SourceCreate / SourceOut / SourceUpdate
    services/                   # SourceService, SchedulerService, SubscriptionService
  infrastructure/
    repositories/               # SourceRepo → implements SourceRepository (session per call)
    rabbit/connector.py         # RabbitConnector → implements NewsPublisher
    collectors/                 # RssCollector / WebCrawlCollector / TelegramCollector
  api/routes/                   # health.py, sources.py (FastAPI routers)
  deps.py                       # composition root — DI wiring
  main.py                       # FastAPI app + lifespan
```

Notes: run uv from here (`uv sync --all-packages`). Each service is its own package
(`pyproject.toml` depending on `common`, plus a `Dockerfile`), and ships a
**uniquely named** top-level package (e.g. `source_service`, not a generic `app`)
so services coexist when the migrator imports their models. New service = copy
`source_service/`, add it to `members` in `pyproject.toml` and a block to the root
`docker-compose.yml`. Models live in the owning service; services never import each
other (share via `common` + the bus) — except `migrator`, which imports each
service's models to build the full schema. Migrations are centralized in `migrator`
— `cd migrator && uv run alembic -c alembic.ini upgrade head` (the compose
`migrator` one-shot does this). A public API gateway is planned
(`../plans/api-gateway.md`); services stay internal until then.
