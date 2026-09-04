# frontend

React SPA — Vite + TypeScript + React Router. No SSR; `build` emits static files.

- `src/` — application source.
- `public/` — static assets served as-is.
- `index.html` — Vite entry HTML.
- `VITE_`-prefixed config lives in the **repo-root `.env`** (see `../.env.example`);
  Compose passes it to the nginx image as a build arg.
- `vite.config.ts`, `tsconfig*.json`, `.oxlintrc.json` — build/TS/lint config.

Notes: `npm run dev` / `build` (→ `dist/`) / `lint` (oxlint). Call the backend via
relative `/api/...` (nginx proxies). Only `VITE_` vars reach the browser — no secrets.
