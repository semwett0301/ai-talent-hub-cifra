# npa_service

Tracks legislative acts from State Duma bill cards. Registration validates the exact
Duma URL, imports the current stage/title/update date and latest Word bill text, stores an
immutable initial version, and returns the current registry state. A daily job revisits
active acts; stage or text-document changes create a new version and are explained by
OpenRouter/DeepSeek in plain Russian. Official publication moves the act into the
terminal `published` State and stops further checks.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — HTTP/HTML/DOCX, scheduler, and structured LLM dependencies; ships
  the uniquely named top-level package `npa_service`.
- `npa_service/`
  - `main.py` — FastAPI app. Routers own paths from the root; nginx maps `/api/npa/*`
    onto them (`root_path = settings.edge.npa_api_prefix`, so `/api/npa/docs` works behind
    nginx). Its lifespan starts/stops the daily scheduler and shared Duma client.
  - `deps.py` — composition root for catalog, registration, monitor, source, model, and
    scheduler.
  - `domain/` — snapshots/change values and the tracking State pattern.
  - `application/` — DTOs, typed failures, ports, and catalog/registration/monitor use cases.
  - `infrastructure/` — SQL repository, allow-listed Duma + DOCX adapter, structured
    OpenRouter adapter, and APScheduler adapter.
  - `api/routes/` — FastAPI routers only: `npa.py` (`GET /`, `GET /{id}`, `POST /`),
    `health.py`.

`POST /` accepts only `url`; additional legacy candidate fields from `news_service` are
ignored. A repeated URL is a DB-enforced 409. Current state lives in `npa`; full texts and
change explanations live in `npa_version`. Tests use representative HTML/in-memory DOCX
and fake ports, so CI never contacts the Duma site or OpenRouter.

For a browser-level local demonstration, set `NPA_SIMULATION_ENABLED=true` and
`NPA_POLL_INTERVAL_SECONDS=5`. Add `https://sozd.duma.gov.ru/bill/9999999-9` in the
UI: it produces an initial draft, a changed version after one interval, then a published
version after the next interval. Repeat with a different final digit (for example,
`9999999-10`) to create a new local test record. The simulated source and summaries never
call the Duma site or OpenRouter. Keep this switch disabled outside local development.
