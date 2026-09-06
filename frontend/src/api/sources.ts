import type { components } from "./schema.sources"

export type Source = components["schemas"]["SourceOut"]
export type SourceType = components["schemas"]["SourceType"]
export type SourceReliability = components["schemas"]["SourceReliability"]

export const TYPE_LABELS: Record<SourceType, string> = {
  telegram: "Telegram",
  rss: "RSS",
  web: "Сайт",
}

// How much the analyst trusts what this source reports — curated, never inferred.
export const RELIABILITY_LABELS: Record<SourceReliability, string> = {
  high: "Высокая",
  medium: "Средняя",
  low: "Низкая",
}

export const DEFAULT_RELIABILITY: SourceReliability = "medium"

export function isReliability(value: string): value is SourceReliability {
  return value in RELIABILITY_LABELS
}

// The intervals the UI offers; the DB stores plain seconds, so the list lives here. The
// first one is what the server assigns a new pull source (SOURCE_POLL_INTERVAL_SECONDS).
export const FREQUENCIES = [
  { seconds: 300, label: "Каждые 5 минут" },
  { seconds: 1800, label: "Каждые 30 мин" },
  { seconds: 3600, label: "Каждый час" },
  { seconds: 10800, label: "Каждые 3 часа" },
  { seconds: 28800, label: "Каждые 8 часов" },
  { seconds: 86400, label: "Каждые 24 часа" },
  { seconds: 259200, label: "Каждые 3 дня" },
  { seconds: 604800, label: "Каждую неделю" },
  { seconds: 2592000, label: "Каждый месяц" },
  { seconds: 7776000, label: "Каждый квартал" },
] as const

export const REALTIME_LABEL = "В реальном времени"

/** Telegram is a push source — it streams, so it has no interval to pick. */
export function isScheduled(source: Pick<Source, "type">): boolean {
  return source.type !== "telegram"
}

/** An interval the server chose that the list doesn't offer still needs an option. */
export function frequencyOptions(seconds: number | null): { value: string; label: string }[] {
  const known = FREQUENCIES.map(({ seconds: value, label }) => ({
    value: String(value),
    label,
  }))
  if (seconds === null || FREQUENCIES.some((option) => option.seconds === seconds)) return known

  return [{ value: String(seconds), label: `Каждые ${seconds} с` }, ...known]
}
