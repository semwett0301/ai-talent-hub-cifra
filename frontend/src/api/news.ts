import type { components, operations } from "./schema.news"

export type NewsOut = components["schemas"]["NewsOut"]
export type NewsListParams = NonNullable<operations["list_news__get"]["parameters"]["query"]>
export type NewsVisibility = components["schemas"]["NewsVisibility"]
export type NewsRelevance = components["schemas"]["NewsRelevanceOut"]
export type ImpactReason = components["schemas"]["ImpactReasonOut"]
export type RelevanceCategory = components["schemas"]["RelevanceCategory"]

/** The tone a card and its badge take per relevance category (a CSS modifier). */
export type RelevanceTone = "critical" | "warning" | "normal" | "low"
export const RELEVANCE_TONES: Record<RelevanceCategory, RelevanceTone> = {
  "требует внимания": "critical",
  важно: "warning",
  релевантно: "normal",
  "низкая релевантность": "low",
}
// The ranker's urgency bases, as the details read them.
export const URGENCY_LABELS: Record<string, string> = {
  not_urgent: "Без срочности",
  over_30_days: "Срок более 30 дней",
  within_4_30_days: "Срок 4–30 дней",
  within_3_days: "Срок до 3 дней",
  already_happened: "Уже произошло",
  breaking: "Срочно",
}
export const DIMENSION_LABELS: Record<ImpactReason["dimension"], string> = {
  finance: "Финансы",
  reputation: "Репутация",
  technology: "Технологии",
  competition: "Конкуренция",
}
export const IMPACT_SCORE_MAX = 3

/** The impact dimensions the model found a company consequence in, strongest first. */
export function impactReasons(relevance: NewsRelevance): ImpactReason[] {
  return relevance.impact
    .filter((reason) => reason.score > 0)
    .sort((left, right) => right.score - left.score)
}

/** "важно · 68" — the category with the rounded score, as the badge reads. */
export function relevanceLabel(relevance: NewsRelevance): string {
  return `${relevance.category} · ${Math.round(relevance.score)}`
}

// The feed's periods, as the filter offers them. The server takes an absolute `since`.
export const PERIODS = [
  { hours: 24, label: "За 24 часа" },
  { hours: 48, label: "За 2 дня" },
  { hours: 72, label: "За 3 дня" },
] as const
export const DEFAULT_PERIOD_HOURS = 72

const HOUR_MS = 60 * 60 * 1000
const MINUTE_MS = 60 * 1000
export const EXCERPT_LENGTH = 160

/** The period's start, rounded down to the minute so the query key stays stable across renders. */
export function sinceHoursAgo(hours: number, now = Date.now()): string {
  const start = now - hours * HOUR_MS

  return new Date(start - (start % MINUTE_MS)).toISOString()
}

/** When the item happened: its publication, else when we collected it. */
export function newsMoment(item: Pick<NewsOut, "published_at" | "created_at">): Date {
  return new Date(item.published_at ?? item.created_at)
}

const TIME = new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" })
const DAY = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" })

function isSameDay(left: Date, right: Date): boolean {
  return left.toDateString() === right.toDateString()
}

/** "09:40" today, "Вчера, 16:30", otherwise "3 сентября" — as the cards always read. */
export function formatMoment(moment: Date, now = new Date()): string {
  if (isSameDay(moment, now)) return TIME.format(moment)

  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (isSameDay(moment, yesterday)) return `Вчера, ${TIME.format(moment)}`

  return DAY.format(moment)
}

export function formatToday(now = new Date()): string {
  return `Сегодня, ${DAY.format(now)}`
}

/** The card's teaser: the source's own blurb, else the start of the text. */
export function excerptOf(item: Pick<NewsOut, "excerpt" | "text">): string {
  if (item.excerpt) return item.excerpt

  const text = item.text.trim()
  return text.length > EXCERPT_LENGTH ? `${text.slice(0, EXCERPT_LENGTH).trimEnd()}…` : text
}
