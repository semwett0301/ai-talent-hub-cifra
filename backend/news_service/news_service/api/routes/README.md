# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `news.py` — the news API at the root (nginx mounts the service under `/api/news`),
  using the `get_news_feed` / `get_npa_escalation` dependencies (from root `deps.py`).
  `GET /` reads a `NewsQuery` off the query string (`q` — ILIKE over title and text,
  `since`, `visibility` — `visible` (default) / `dismissed` / `all`) and answers the
  matches as a `NewsOut[]` — one item per event cluster (duplicates left out), newest
  publication first, no paging; each carries the pipeline's `summary` and `relevance`
  (null until ranked). `GET /{news_id}` — one item or **404**. `POST /{news_id}/dismiss` / `POST /{news_id}/restore` set / clear
  `dismissed_at` and return the item (**404** unknown). `POST /{news_id}/npa` takes an
  optional `NpaDTO` body (else the act is built from the item), flags `is_alert` **and**
  registers the act in `npa_service` atomically; **404** unknown id, **409** the act's
  `url` already exists there, **502** `npa_service` unreachable or failed (in both error
  cases the flag is left unset). No create/update/delete — rows come only from the bus.

Notes: keep handlers thin — resolve the use case, call it, return a DTO.
