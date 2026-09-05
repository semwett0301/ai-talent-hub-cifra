# source_service (package)

The importable service package. The service itself — what it does, how it is deployed,
the WEB collector — is described in `../README.md`; this file only maps the layers.

- `main.py` — FastAPI app + lifespan (connect infra, load and start the runtime registry).
- `deps.py` — composition root: builds every concrete collaborator and injects it.
- `domain/` — the service's own entities and pure rules (`Article`, `Hub`, scoring,
  URL identity). No I/O.
- `application/` — use cases and ports: `services/` grouped by domain (`source/`,
  `scraping/`, `article/`), `parse/` (pure parsing), `ports/`, `dto/`.
- `infrastructure/` — port implementations: repositories, RabbitMQ, collectors, crawlers.
- `api/` — FastAPI routers.

Notes: dependencies point inward (`api` → `application` → `domain`; `infrastructure`
implements `application.ports`); only `deps.py` knows every layer.
