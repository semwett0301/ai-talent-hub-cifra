# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `sources.py` — CRUD for sources (`/sources`), using the `get_source_service`
  dependency (from root `deps.py`) and `application.dto.source` models.

Notes: keep handlers thin — resolve the use case, call it, return a DTO. The
`_get_or_404` helper centralizes the not-found → 404 mapping.
