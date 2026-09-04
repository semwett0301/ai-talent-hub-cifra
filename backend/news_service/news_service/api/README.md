# api

Outermost layer — FastAPI controllers and HTTP-only concerns. Thin: resolve the use
case (from `deps`), call it, return DTOs. No business logic.

- `routes/` — the endpoints (one `APIRouter` per file), mounted in `main.py`.

Notes: the DI provider (`get_news_feed`) lives in the root `deps.py`; DTOs live in
`application.dto`. Endpoints return `application.dto` models, never ORM objects.
