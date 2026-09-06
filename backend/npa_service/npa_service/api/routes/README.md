# routes

One `APIRouter` per file, mounted in `main.py`.

- `health.py` — `GET /health` liveness probe.
- `npa.py` — paged current-state list; one act with immutable version metadata; URL-only
  State Duma registration. Responses are 404 for an unknown id, 409 for a duplicate URL,
  422 for a non-Duma/invalid card or Word text, and 502 for temporary remote failure.

Notes: keep handlers thin — resolve the use case, call it, return a DTO.
