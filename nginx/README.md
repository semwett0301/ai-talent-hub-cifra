# nginx

The edge — the only service exposed to the host (port 80).

- `Dockerfile` — multi-stage: builds the React SPA (`frontend/`), then serves the
  static `dist/` from `nginx:alpine`. Build context = repo root.
- `nginx.conf` — serves static with SPA fallback to `index.html`.

Notes: no `upstream` block — single backend, so `proxy_pass http://api:8000`
directly. Backend and DB have no host ports; all external traffic goes through here.
