# api

Outermost layer — FastAPI controllers and HTTP-only concerns. Thin: resolve the use
case (from `deps`), call it, return DTOs. No business logic.

- `routes/` — the endpoints (one `APIRouter` per file), mounted in `main.py`.
- `errors.py` — `install_error_handlers(app)`: maps `application.errors` to status codes
  (`SourceAlreadyExistsError` → 409, `SourceNotRelevantError` → 422) once, so routes hold
  no `try/except`. Responses keep FastAPI's own `{"detail": ...}` shape.

Notes: the DI provider (`get_source_service`) lives in the root `deps.py`; DTOs live
in `application.dto`. Endpoints return `application.dto` models, never ORM objects.
