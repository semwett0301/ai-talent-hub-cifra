# frontend

React 19 + Vite + TypeScript SPA, built to static files and served by the `nginx` image
(there is no frontend container). Routes are declared in `src/App.tsx`.

## File map

- `src/api/` — the typed backend client. `schema.sources.d.ts` is **generated** from the
  service's OpenAPI spec (`npm run api:gen`) and committed; `client.ts` builds the
  `openapi-fetch` client plus `openapi-react-query` hooks; `sourceMutations.ts` wraps the
  queries/mutations so every write invalidates the list in one place; `sources.ts` holds
  the view vocabulary (type and reliability labels, the nine poll intervals, the
  realtime/no-schedule labels).
- `src/pages/` — one component per route: `SourcesPage` (live API), `NewsPage` and
  `NpaPage` (still on `src/data/` fixtures).
- `src/components/sources/` — the Sources screen: row, create/edit dialog, delete dialog.
- `src/components/monitoring/Shared.tsx` — `SearchField` and `Choice`.
- `src/components/ui/` — shadcn / Base UI primitives, unchanged.
- `src/data/` — remaining demo fixtures for News and НПА.
- `src/globals.d.ts` — the compile-time API-prefix constants.
- `UI_GUIDELINES.md`, `UI_IMPLEMENTATION.md`, `handoff/` — product and design notes.
- `Dockerfile.dev` — dev-only image for the root `docker-compose.dev.yml`: `npm ci` baked
  in, source bind-mounted, runs `npm run dev -- --host`. The production bundle is built by
  `nginx/Dockerfile`.

## Commands

```bash
npm install
npm run dev            # Vite dev server; /api is proxied to the compose stack
npm run build          # static build → dist/
npm run lint
npm run api:gen        # regenerate src/api/schema.*.d.ts from a running backend
```

## Notes

- **API prefixes are compile-time constants**, not env reads. `SOURCES_API_PREFIX` /
  `NEWS_API_PREFIX` / `NPA_API_PREFIX` come from the repo-root `.env` (via nginx build
  args) and `vite.config.ts` bakes them in as `__SOURCES_API_PREFIX__` and friends. There
  is no `.env` file here — a production build **fails** if a prefix is unset, so a
  misconfigured deploy never ships a bundle pointing at the wrong path.
- `npm run dev` has no nginx in front of it, so `vite.config.ts` proxies `/api` to
  `http://localhost` (override with `DEV_API_TARGET`). Bring the compose stack up first.
  The same dev server can run inside Compose instead (`docker-compose.dev.yml`, root
  README → "Run"); there `DEV_API_TARGET=http://nginx` and `/app/node_modules` is an
  anonymous volume, so restart with `up --build -V` after a `package.json` change.
- `api:gen` reads `$SPEC_URL` (default `http://localhost/api/sources/openapi.json`). It
  runs `openapi-typescript` through `npx` rather than as a devDependency: the tool still
  declares a peer on TypeScript 5.x while this project is on 6.x. `--default-non-nullable
  false` keeps fields that have server-side defaults optional in request bodies.
- The generated file is committed so `npm run build` and CI never need a live backend.
