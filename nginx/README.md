# nginx

The edge — the only service exposed to the host (port 80).

- `Dockerfile` — multi-stage: builds the React SPA (`frontend/`), then serves the
  static `dist/` from `nginx:alpine`. Build context = repo root.
- `templates/default.conf.template` — serves static with SPA fallback to
  `index.html`, and reverse-proxies each backend under its own `/api/<service>/`
  namespace. Currently `/api/sources/*` → `source_service:8000` with the **whole
  `/api/sources` prefix stripped** (`/api/sources` → `/`, `/api/sources/5` → `/5`,
  `/api/sources/openapi.json` → `/openapi.json`), so the OpenAPI spec is reachable
  at `/api/sources/openapi.json`.

Notes: the `.template` file is processed by the nginx image's built-in
docker-entrypoint envsubst step at container start (`*.template` under
`/etc/nginx/templates/` → `/etc/nginx/conf.d/*.conf`), substituting
`${SOURCES_API_PREFIX}` from the container environment — nginx's own
`$`-variables (`$host`, `$remote_addr`, `$scheme`, `$uri`, `$1`, ...) are left
alone since they aren't set as env vars. `SOURCES_API_PREFIX` is defined **once**,
in `docker-compose.yml` (`x-sources-api-prefix` anchor), and shared with
`source_service` (which reads it back as FastAPI's `root_path` via
`common.settings.settings.sources_api_prefix`) — change the prefix there, not here.

The API location is a regex (`~ ^${SOURCES_API_PREFIX}(?:/(.*))?$` + `rewrite …
break`) so it matches the bare collection and sub-paths without a trailing-slash
redirect and never catches `/api/sourcesXYZ`. Common `proxy_set_header`s sit at
`server` scope so each service location only needs `rewrite` + `proxy_pass`; add a
sibling location per new service. No `upstream` block — `proxy_pass
http://source_service:8000` directly (compose DNS); nginx `depends_on`
source_service so the host resolves at startup. Backend and DB have no host ports;
all external traffic goes through here.

`merge_slashes off` is set at `server` scope: a source's id is its `link` (a full
URL), so `/api/sources/{link}` legitimately contains `//` (e.g.
`/api/sources/https://t.me/x`) — nginx's default `merge_slashes on` would collapse
that before location matching and break the route.
