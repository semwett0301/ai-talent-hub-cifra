# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `news.py` — the news API at the root (nginx mounts the service under `/api/news`),
  using the `get_news_feed` / `get_npa_escalation` dependencies (from root `deps.py`)
  and `NewsOut`. `GET /` pages with `limit` (default 50, max 500) and `offset`, newest
  first. `POST /{news_id}/dismiss` sets `is_alert = true` and returns the item, or
  **404** for an unknown id. `POST /{news_id}/npa` takes an `NpaDTO` body, dismisses
  the item **and** registers the act in `npa_service` atomically; **404** unknown id,
  **409** the act's `url` already exists there, **502** `npa_service` unreachable or
  failed (in both error cases the alert is left undismissed). No create/update/delete
  — rows come only from the bus.

Notes: keep handlers thin — resolve the use case, call it, return a DTO.
