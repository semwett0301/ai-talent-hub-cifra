# api

Outermost layer — FastAPI controllers and HTTP-only concerns. Thin: resolve the use
case (from `deps`), call it, return DTOs. No business logic.

- `routes/` — the endpoints (one `APIRouter` per file), mounted in `main.py`.

Notes: DI providers for catalog reads and registration live in root `deps.py`; endpoints
return application DTOs, never ORM objects.
