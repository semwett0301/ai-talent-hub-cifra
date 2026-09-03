# nginx

The edge — the only service exposed to the host (port 80).

- `Dockerfile` — multi-stage: builds the React SPA (`frontend/`), then serves the
  static `dist/` from `nginx:alpine`. Build context = repo root.
- `nginx.conf` — serves static with SPA fallback to `index.html`, and reverse-proxies
  `/api/*` → `source_service:8000` (the `/api` prefix is stripped, so `/api/sources`
  → `/sources`).

Notes: no `upstream` block — `proxy_pass http://source_service:8000/` directly
(compose DNS). Backend and DB have no host ports; all external traffic goes through
here. nginx `depends_on` source_service so the upstream host resolves at startup.
