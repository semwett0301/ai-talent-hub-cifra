# api

- `npa.ts` — typed registry, detail/version-history reads and URL registration through
  the nginx NPA prefix. It maps snake-case DTOs into UI models and turns HTTP status
  codes into Russian user-facing errors (`npaErrorMessage`, reused by the news-escalation
  flow in `NewsPage` since both ultimately hit npa_service).
- `news.ts` — `NewsOut`/`NewsListParams` types off the generated news schema, period
  presets, and the moment/excerpt formatting shared by `NewsPage`'s tabs (including its
  `is_alert` one).
- `newsMutations.ts` — `openapi-react-query` hooks over the news schema: `useNews`
  (list), `useDismissNews` / `useRestoreNews`, and `useEscalateNpa` (flags a news item as
  an alert and registers it in npa_service — invalidates both the news and npa lists).
- `client.ts` — the generated `sourcesApi` / `newsApi` query clients and shared HTTP
  error helpers (`errorStatus`, `errorMessage`).
