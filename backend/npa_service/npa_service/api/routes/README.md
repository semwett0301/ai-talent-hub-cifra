# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `npa.py` — the acts API at the root (nginx mounts the service under `/api/npa`),
  using the `get_npa_catalog` dependency (from root `deps.py`) and `NpaOut`. `GET /`
  pages with `limit` (default 50, max 500) and `offset`, newest first. `GET /{npa_id}`
  returns one act or **404**. `POST /` takes the shared `NpaDTO` and returns **201**
  with the stored act, or **409** when the `url` is already stored.

Notes: keep handlers thin — resolve the use case, call it, return a DTO.
