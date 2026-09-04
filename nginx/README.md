# nginx

The edge — the only service exposed to the host (port 80).

- `Dockerfile` — multi-stage: builds the React SPA (`frontend/`), then serves the
  static `dist/` from `nginx:alpine`. Build context = repo root.
- `nginx.conf` — serves static with SPA fallback to `index.html`, and reverse-proxies
  each backend under its own `/api/<service>/` namespace. Currently `/api/sources/*`
  → `source_service:8000` with the **whole `/api/sources` prefix stripped**
  (`/api/sources` → `/`, `/api/sources/5` → `/5`, `/api/sources/openapi.json` →
  `/openapi.json`), so the OpenAPI spec is reachable at `/api/sources/openapi.json`.

Notes: the API location is a regex (`~ ^/api/sources(?:/(.*))?$` + `rewrite … break`)
so it matches the bare collection and sub-paths without a trailing-slash redirect and
never catches `/api/sourcesXYZ`. Common `proxy_set_header`s sit at `server` scope so
each service location only needs `rewrite` + `proxy_pass`; add a sibling location per
new service. No `upstream` block — `proxy_pass http://source_service:8000` directly
(compose DNS); nginx `depends_on` source_service so the host resolves at startup.
Backend and DB have no host ports; all external traffic goes through here.
