# npa_service package

- `main.py` — API lifespan, scheduler startup/shutdown, and routers.
- `deps.py` — the only composition root for repositories, Duma HTTP, OpenRouter, and
  scheduler implementations.
- `domain/` — immutable bill/change values and tracking State behavior.
- `application/` — ports, use cases, DTOs, and typed failures.
- `infrastructure/` — database, Duma/DOCX, OpenRouter, and scheduling adapters.
- `api/` — thin FastAPI routes.

Dependencies point inward; external I/O occurs only in infrastructure behind application
ports. See the parent README for runtime behavior and configuration.
