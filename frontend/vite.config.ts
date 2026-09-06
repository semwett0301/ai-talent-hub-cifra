import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// Each service's nginx location, defined once in the repo-root .env and passed in as a
// build arg; the fallback is what the compose stack serves locally.
const API_PREFIXES = {
  __SOURCES_API_PREFIX__: ["SOURCES_API_PREFIX", "/api/sources"],
  __NEWS_API_PREFIX__: ["NEWS_API_PREFIX", "/api/news"],
  __NPA_API_PREFIX__: ["NPA_API_PREFIX", "/api/npa"],
} as const

// Baked into the bundle, so a missing value must fail the build, never default silently.
function apiPrefixDefines(isBuild: boolean): Record<string, string> {
  return Object.fromEntries(
    Object.entries(API_PREFIXES).map(([token, [name, devFallback]]) => {
      const value = process.env[name]
      if (isBuild && !value) throw new Error(`${name} is required for a production build`)

      return [token, JSON.stringify(value ?? devFallback)]
    })
  )
}

export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  define: apiPrefixDefines(command === "build"),
  // No nginx in front of the dev server, so /api has to be forwarded to the compose stack.
  server: {
    proxy: {
      "/api": process.env.DEV_API_TARGET ?? "http://localhost",
    },
  },
}))
