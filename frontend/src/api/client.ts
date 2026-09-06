import createFetchClient from "openapi-fetch"
import type { Middleware } from "openapi-fetch"
import createQueryClient from "openapi-react-query"

import type { paths as NewsPaths } from "./schema.news"
import type { paths as SourcesPaths } from "./schema.sources"

export const CONFLICT = 409

const GENERIC_ERROR = "Что-то пошло не так. Попробуйте ещё раз."
const MESSAGE_BY_STATUS: Record<number, string> = {
  [CONFLICT]: "Источник с таким адресом уже добавлен.",
}

// openapi-react-query throws the parsed body and nothing else, so the status — the only
// thing the UI branches on — has to travel inside it.
const statusInBody: Middleware = {
  async onResponse({ response }) {
    if (response.ok) return response

    return new Response(JSON.stringify({ status: response.status }), {
      status: response.status,
      headers: { "content-type": "application/json" },
    })
  },
}

// Each service's nginx location, baked in by vite.config.ts from the repo-root .env.
const sourcesFetch = createFetchClient<SourcesPaths>({ baseUrl: __SOURCES_API_PREFIX__ })
const newsFetch = createFetchClient<NewsPaths>({ baseUrl: __NEWS_API_PREFIX__ })
sourcesFetch.use(statusInBody)
newsFetch.use(statusInBody)

export const sourcesApi = createQueryClient(sourcesFetch)
export const newsApi = createQueryClient(newsFetch)

export function errorStatus(error: unknown): number | undefined {
  const status = (error as { status?: unknown } | undefined)?.status

  return typeof status === "number" ? status : undefined
}

/** What to tell the user, chosen by status — never by the server's own English prose. */
export function errorMessage(error: unknown): string {
  const status = errorStatus(error)

  return (status !== undefined && MESSAGE_BY_STATUS[status]) || GENERIC_ERROR
}
