# source_service

Ingestion service: **CRUD sources → collect news → publish to RabbitMQ**. No
persistent dedupe, no news storage — downstream consumes from RabbitMQ and dedupes on
`NewsDTO.url`. Telegram (kurigram), RSS (feedparser + news-please), and WEB
sources are implemented. WEB sources use the embedded
`infrastructure.crawling.news_agent` through `WebCrawlCollector`.
Design: `../../../plans/source-service-architecture.md`,
`../../../plans/telegram-kurigram-migration.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `domain` + fastapi, aio-pika, apscheduler, kurigram,
  crawl4ai, feedparser, news-please. Ships a uniquely named top-level package
  `source_service`.
- `source_service/`
  - `main.py` — FastAPI app + lifespan; builds collaborators via `deps` and runs
    them. Routers own paths from the root; nginx maps `/api/sources/*` onto them, so
    the OpenAPI spec is reachable at `/api/sources/openapi.json`. (No `root_path`, so
    the Swagger UI at `/api/sources/docs` won't auto-load the spec through nginx —
    use it against the service directly in dev.)
  - `deps.py` — **composition root**: builds collector registries + repository +
    publisher and injects them into application (all DI lives here). Data shapes are
    shared: `Source` (ORM) from `domain.schemas`, `NewsDTO` from `domain.entities.news`.
  - `application/` — `ports/` (interfaces infra implements) + `dto/` + `services/` +
    `parse/`: `SourceService` (CRUD over the repo port; auto-detects a source's
    `type` from its `link` via `parse/` + the `PageFetcher` port — clients never
    send `type`; an RSS feed's URL is stored in `rss_link`, scraping-only and also
    never client-supplied) and `SourceRegistry` (the runtime registrar — pull
    scheduling + push subscription, kept in sync with CRUD).
  - `infrastructure/` — port implementations: `repositories/` (`SourceRepo`, a
    session per call), `rabbit/` (`RabbitConnector`), `collectors/`
    (`Rss`/`WebCrawl`/`Telegram`), `crawlers/` (`Crawl4AiPageFetcher`, the one HTTP
    fetch, + `FeedparserFeedReader`).
  - `api/routes/` — FastAPI routers only: `sources.py` (CRUD), `health.py`.

Notes: pull collectors run on `poll_interval_seconds`, falling back to
`SOURCE_POLL_INTERVAL_SECONDS` (300s) when the row has none; push sources
are subscribed at startup. CRUD stays live — create/update/delete reconcile the
runtime through the `SourceRegistry` composite (stored on `app.state.registrar`), so
sources (un)schedule/(un)subscribe without a restart. Filling in a collector =
implement `fetch`/`subscribe` in its infra file; register it in `deps`.

## WEB collector

`WebCrawlCollector` is a `PullCollector`: for each `WEB` source it starts one
Crawl4AI pipeline, discovers news/listing links, extracts fresh articles and
publishes one `NewsDTO` per article to `news.raw.web`. The compact shared fields
are `url`, `text`, `published_at` and source attributes. All agent data is kept
as JSON under `raw`: convenient keys include `title`, `author`, `description`,
`image_url`, `canonical_url`, `date_source` and `date_evidence`; the complete
serialised `ArticleRecord` is `raw.article`.

The LLM is used only when it has credentials: for ambiguous publication dates
and to classify listing pages. Without credentials the deterministic
HTML/JSON-LD/Crawl4AI path remains active; the collector does not make failing
LLM requests. `WEB_CRAWL_MAX_ARTICLES` bounds work per scheduled source run
(default 50), and `WEB_CRAWL_DAYS` selects the publication window (default 3).

For a local test, install dependencies and Chromium once, then run the focused
test suite:

```bash
cd backend
uv sync --all-packages --group dev
uv run playwright install chromium
DEBUG=true uv run pytest source_service/tests
```

To make a live crawl without waiting for the scheduler, with the service stack
already running:

```bash
docker compose exec -T source_service python -c '
import asyncio
from domain.entities.news import SourceType
from domain.entities.source import SourceReliability
from domain.schemas import Source
from source_service.infrastructure.collectors import WebCrawlCollector
source = Source(name="Crawl smoke test", link="https://example.com", type=SourceType.WEB, reliability=SourceReliability.MEDIUM)
items = asyncio.run(WebCrawlCollector().fetch(source))
print(f"collected={len(items)}")
for item in items[:3]: print(item.url, item.raw["title"])
'
```

Replace `https://example.com` with a real news site that you are authorised to
crawl. For normal operation create the source through `POST /api/sources/` with
`poll_interval_seconds`; check that the response has `"type": "web"`, then
watch `docker compose logs -f source_service` for `web crawl finished` and
`news published`.
The `Source` table and every ORM model live in the shared `domain.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
