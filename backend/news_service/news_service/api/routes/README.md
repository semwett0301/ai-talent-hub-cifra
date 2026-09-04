# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `news.py` — read API for news at the root (nginx mounts the service under
  `/api/news`), using the `get_news_feed` dependency (from root `deps.py`) and
  `NewsOut`. `GET /` pages with `limit` (default 50, max 500) and `offset`, newest
  first. `POST /{news_id}/dismiss` sets `is_alert = true` and returns the item, or
  **404** for an unknown id. No create/update/delete — rows come only from the bus.

Notes: keep handlers thin — resolve the use case, call it, return a DTO.
