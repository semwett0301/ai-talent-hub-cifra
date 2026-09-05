# nginx

The edge — the only service exposed to the host (port 80).

- `Dockerfile` — multi-stage: builds the React SPA (`frontend/`), then serves the
  static `dist/` from `nginx:alpine`. Build context = repo root.
- `templates/default.conf.template` — serves static with SPA fallback to
  `index.html`, reverse-proxies each backend under its own `/api/<service>/`
  namespace, and proxies `${LOGS_PREFIX}/` (default `/logs/`) to Dozzle (login is
  Dozzle's own, see `../dozzle/README.md`). Currently `/api/sources/*` → `source_service:8000` with the **whole
  `/api/sources` prefix stripped** (`/api/sources` → `/`, `/api/sources/5` → `/5`,
  `/api/sources/openapi.json` → `/openapi.json`), so the OpenAPI spec is reachable
  at `/api/sources/openapi.json`; likewise `/api/news/*` → `news_service:8000`
  (`${NEWS_API_PREFIX}`) and `/api/npa/*` → `npa_service:8000` (`${NPA_API_PREFIX}`).
Notes: the `.template` file is processed by the nginx image's built-in
docker-entrypoint envsubst step at container start (`*.template` under
`/etc/nginx/templates/` → `/etc/nginx/conf.d/*.conf`), substituting
`${SOURCES_API_PREFIX}` from the container environment — nginx's own
`$`-variables (`$host`, `$remote_addr`, `$scheme`, `$uri`, `$1`, ...) are left
alone since they aren't set as env vars. `SOURCES_API_PREFIX` is defined **once**,
in the repo-root `.env` (see `../.env.example`), and shared with
`source_service` (which reads it back as FastAPI's `root_path` via
`domain.core.settings.settings.sources_api_prefix`) — change the prefix there, not here.

The API location is a regex (`~ ^${SOURCES_API_PREFIX}(?:/(.*))?$` + `rewrite …
break`) so it matches the bare collection and sub-paths without a trailing-slash
redirect and never catches `/api/sourcesXYZ`. Common `proxy_set_header`s sit at
`server` scope so each service location only needs `rewrite` + `proxy_pass`; add a
sibling location per new service. No `upstream` block — the backend address goes
through a variable (`set $sources_backend ...` + `proxy_pass $sources_backend`)
with `resolver 127.0.0.11` (Docker's embedded DNS), so nginx re-resolves it per
request and follows a restarted container's new IP instead of pinning to the one it
saw at startup. Because `proxy_pass` has a variable and no URI
part, the URI produced by the preceding `rewrite ... break` is what gets passed —
hence `set` must come before the `rewrite`. Backend and DB have no host ports; all
external traffic goes through here.

The `/logs` location keeps the prefix (no `rewrite`) because Dozzle is started with
`DOZZLE_BASE=${LOGS_PREFIX}` and serves its assets under it. It streams over SSE /
WebSocket, hence `proxy_buffering off`, `proxy_read_timeout 1h`, `proxy_http_version
1.1` and the `Upgrade`/`Connection` passthrough via the `map $http_upgrade
$connection_upgrade` block at the top of the template (a `map` must live in the
`http` context, which `conf.d/*.conf` is included into). `location = ${LOGS_PREFIX}`
only redirects to the trailing-slash form.
