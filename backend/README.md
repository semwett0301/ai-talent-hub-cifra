# backend

All Python code, as one uv workspace. The workspace root is virtual (declares no
package); the shared kernel and each deployable service are sibling member
directories (no `services/` wrapper).

- `domain/` — shared kernel member (its own `pyproject.toml`; package at
  `domain/domain/`, imported as `domain`): `core/` = settings + logging + DB + shared Rabbit batch consumer,
  `entities/` = business shapes (grouped by domain, e.g. `entities/news`), `schemas/`
  = the shared ORM models. Because the DB is one for all services, schemas live here.
- `source_service/` — ingestion service: CRUD sources, collect news (Telegram push
  + RSS pull implemented, Web crawl a stub), publish to RabbitMQ. See `../plans/source-service-architecture.md`.
- `news_service/` — consumer service: reads the `news` exchange in batches (prefetch +
  deferred ack), stores each `NewsDTO` once per `url` in the `news` table, serves
  list + dismiss on `/api/news`; `POST /{id}/npa` escalates an alert into a
  legislative act (dismiss + synchronous create in `npa_service`, atomically).
  See `../plans/news-service.md`.
- `npa_service/` — legislative-acts (НПА) service: stores `NpaDTO`s once per `url` in
  the `npa` table, serves list / get / create on `/api/npa`. See `../plans/npa-service.md`.
- `migrator/` — one-shot Alembic runner that owns the shared DB schema history (one
  database for all services). Runs `upgrade head` on boot, then exits.
- `pyproject.toml` — virtual workspace root: `[tool.uv.workspace] members` (domain +
  the services) + shared dev tooling (ruff/mypy/pytest). No package of its own.
- `uv.lock` — locked versions (committed).
- Settings come from the **repo-root `.env`** (see `../.env.example`); `domain.core.settings`
  loads it by absolute path, so `uv run` works from any directory.

## Service architecture — onion / clean layers

Each service is structured as **onion architecture**: dependencies point **inward**,
toward the shared `domain`. Outer layers depend on inner ones, never the reverse; the
concrete wiring happens once, at the composition root.

| Layer | Holds | Depends on |
|-------|-------|-----------|
| `domain` (shared) | ORM **schemas** (`Source`, `News`, `Npa`) + business **entities** (`NewsDTO`, `NpaDTO`) + `core` infra. Shared across all services. | SQLAlchemy / pydantic |
| `application/` | Use cases / orchestration, the **ports** (interfaces) infra implements, and DTOs. | domain |
| `infrastructure/` | Implementations of the ports: repositories, RabbitMQ, collectors (feedparser / Playwright / kurigram), external APIs. | application, domain |
| `api/` | FastAPI routes / controllers and HTTP-only types. | application |
| `deps.py` | **Composition root** — builds the concrete implementations and injects them into application (registry, repository, publisher). | everything |

Inversion in practice: application defines a `Protocol` port (`SourceRepository`,
`NewsPublisher`, `PullCollector`/`PushCollector`, `SourceRegistrar`); infrastructure
supplies a class that **implements** it (inherits the port); `deps.py` constructs the
impl and passes it in. Application never imports a concrete infra class — only its own
ports. The ports type against the shared `domain.schemas.Source` and
`domain.entities.news.NewsDTO` directly.

`source_service/` folder layout:

```
source_service/                 # the importable package
  application/
    ports/                      # collectors.py, repositories.py, publisher.py, registrar.py, crawler.py (Protocols)
    dto/source/                 # SourceCreate / SourceOut / SourceUpdate
    services/                   # SourceService (CRUD), SourceRegistry (runtime registrar)
    parse/                      # pure parsing — telegram.py, rss.py (recognition), article.py (news-please)
  infrastructure/
    repositories/               # SourceRepo → implements SourceRepository (session per call)
    rabbit/connector.py         # RabbitConnector → implements NewsPublisher
    collectors/                 # RssCollector / WebCrawlCollector / TelegramCollector
    crawlers/                   # Crawl4AiPageFetcher → PageFetcher; FeedparserFeedReader → FeedReader
  api/routes/                   # health.py, sources.py (FastAPI routers)
  deps.py                       # composition root — DI wiring
  main.py                       # FastAPI app + lifespan
```

`news_service/` mirrors it, with the bus as an *entry point* instead of an exit: the
shared `domain.core.rabbit.RabbitBatchConsumer` (built in `deps.py`) calls the
inward-facing port `application.ports.NewsBatchHandler`, implemented by
`application.services.NewsIngestor`, which writes through `NewsRepository`
(`infrastructure/repositories/news_repo.py`). The consumer mechanism lives in `domain`
so the next bus consumer service only supplies its model, handler, and config.
`news_service` also has one *outbound* HTTP port, `application.ports.NpaGateway`
(implemented by `infrastructure/gateways/npa_http_gateway.py` over httpx), through
which `NpaEscalation` registers an act in `npa_service` — services still never import
each other; the payload is the shared `domain.entities.npa.NpaDTO`.

`npa_service/` is the plain CRUD shape: `NpaCatalog` (list / get / create) over the
`NpaRepository` port, `NpaRepo` in infrastructure, one router in `api/routes/npa.py`.

Notes: run uv from here (`uv sync --all-packages`). Each service is its own package
(`pyproject.toml` depending on `domain`, plus a `Dockerfile`), and ships a
**uniquely named** top-level package (e.g. `source_service`, not a generic `app`).
New service = copy `source_service/`, add it to `members` in `pyproject.toml` and a
block to the root `docker-compose.yml`. ORM models live in the shared `domain.schemas`
(one DB for all); services never import each other (share via `domain` + the bus), and
the `migrator` imports only `domain.schemas`. Migrations are centralized in `migrator`
— `cd migrator && uv run alembic -c alembic.ini upgrade head` (the compose `migrator`
one-shot does this). A public API gateway is planned (`../plans/api-gateway.md`);
services stay internal until then.
