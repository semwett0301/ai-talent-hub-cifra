import type { components } from "./schema.sources"

export type Source = components["schemas"]["SourceOut"]
export type SourceType = components["schemas"]["SourceType"]

export const TYPE_LABELS: Record<SourceType, string> = {
  telegram: "Telegram",
  rss: "RSS",
  web: "Сайт",
}

// The nine intervals the UI offers; the DB stores plain seconds, so the list lives here.
export const FREQUENCIES = [
  { seconds: 1800, label: "каждые 30 мин" },
  { seconds: 3600, label: "каждый час" },
  { seconds: 10800, label: "каждые 3 часа" },
  { seconds: 28800, label: "каждые 8 часов" },
  { seconds: 86400, label: "каждые 24 часа" },
  { seconds: 259200, label: "каждые 3 дня" },
  { seconds: 604800, label: "каждую неделю" },
  { seconds: 2592000, label: "каждый месяц" },
  { seconds: 7776000, label: "каждый квартал" },
] as const

export const DEFAULT_FREQUENCY = FREQUENCIES[0].seconds
const REALTIME_LABEL = "в реальном времени"
const NO_SCHEDULE_LABEL = "—"

/** Telegram is a push source — it has no interval to show, it streams. */
export function isScheduled(source: Pick<Source, "type">): boolean {
  return source.type !== "telegram"
}

export function frequencyLabel(source: Source): string {
  if (!isScheduled(source)) return REALTIME_LABEL
  if (!source.is_relevant) return NO_SCHEDULE_LABEL

  const match = FREQUENCIES.find((option) => option.seconds === source.poll_interval_seconds)

  return match?.label ?? `каждые ${source.poll_interval_seconds ?? DEFAULT_FREQUENCY} с`
}
