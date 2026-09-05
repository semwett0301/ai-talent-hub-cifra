# npa_service

Legislative-acts service (НПА — нормативно-правовые акты): stores acts in the `npa`
table, once per `url` (the DB's unique key), and serves a small API — list, get one,
create. Acts arrive either directly (`POST /`) or from `news_service`, which posts the
same `NpaDTO` when a reader escalates a news alert into an act. Design:
`../../plans/npa-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `domain` + fastapi, uvicorn. Ships a uniquely named
  top-level package `npa_service`.
- `npa_service/`
  - `main.py` — FastAPI app. Routers own paths from the root; nginx maps `/api/npa/*`
    onto them (`root_path = settings.npa_api_prefix`, so `/api/npa/docs` works behind
    nginx). No lifespan — nothing long-lived to start.
  - `deps.py` — **composition root**: builds `NpaRepo` and provides `get_npa_catalog`
    for the routes.
  - `application/` — `ports/` (`NpaRepository`) + `dto/npa/` (`NpaOut`) +
    `services/` (`NpaCatalog` list / get / create) + `errors.py`
    (`NpaAlreadyExistsError`).
  - `infrastructure/` — port implementations: `repositories/` (`NpaRepo`, a session
    per call).
  - `api/routes/` — FastAPI routers only: `npa.py` (`GET /`, `GET /{id}`, `POST /`),
    `health.py`.

Notes: the request body of `POST /` is the shared `domain.entities.npa.NpaDTO` — the
same contract `news_service` speaks, so there is no separate input DTO. A repeated
`url` is a **409**, enforced by the DB unique key (the repo maps `IntegrityError`).
The `Npa` table and every ORM model live in the shared `domain.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
