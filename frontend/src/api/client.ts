import createFetchClient from "openapi-fetch"
import createQueryClient from "openapi-react-query"

import type { paths as SourcesPaths } from "./schema.sources"

// Each service's nginx location, baked in by vite.config.ts from the repo-root .env.
const sourcesFetch = createFetchClient<SourcesPaths>({ baseUrl: __SOURCES_API_PREFIX__ })

export const sourcesApi = createQueryClient(sourcesFetch)

/** The `{ detail }` body both FastAPI's HTTPException and our error handlers return. */
export function errorDetail(error: unknown, fallback: string): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail

  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg

  return fallback
}
