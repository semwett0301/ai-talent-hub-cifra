// Stand-ins for what the LLM stage will produce. The feed is live, but relevance,
// priority, kind, summary and impact do not exist yet — so every item gets stable
// made-up values (seeded by its id, so a card never changes between renders) and the
// screen keeps its full layout. Replace with `analysis` fields when the pipeline lands.

import { excerptOf, type NewsOut } from "@/api/news"
import type { Priority } from "@/types/monitoring"

export type NewsKind = "НПА" | "Новости"

export interface PlaceholderAnalysis {
  relevance: number
  priority: Priority
  kind: NewsKind
  summary: string
  impact: string
  isPlaceholder: true
}

export type NewsItemView = NewsOut & PlaceholderAnalysis

const RELEVANCE_MIN = 40
const RELEVANCE_SPAN = 56
const CRITICAL_FROM = 85
const WARNING_FROM = 70
const NPA_EVERY = 3

const IMPACTS = [
  "Оценить влияние на продуктовые процессы и договорные обязательства; назначить ответственного за анализ.",
  "Сигнал для продуктовой и коммерческой команд: собрать запросы партнёров и оценить возможности. Срочных действий не требуется.",
  "Проверить соответствие текущих практик новым требованиям и обновить внутреннюю документацию.",
  "Информационный материал: отслеживать развитие темы, регуляторных действий пока не требуется.",
]

/** FNV-1a over the id — a cheap, stable seed with no dependency. */
function seedOf(id: string): number {
  let hash = 0x811c9dc5
  for (let index = 0; index < id.length; index += 1) {
    hash ^= id.charCodeAt(index)
    hash = Math.imul(hash, 0x01000193) >>> 0
  }
  return hash
}

function priorityOf(relevance: number): Priority {
  if (relevance >= CRITICAL_FROM) return "critical"
  if (relevance >= WARNING_FROM) return "warning"
  return "normal"
}

export function withPlaceholders(item: NewsOut): NewsItemView {
  const seed = seedOf(item.id)
  const relevance = RELEVANCE_MIN + (seed % RELEVANCE_SPAN)

  return {
    ...item,
    relevance,
    priority: priorityOf(relevance),
    kind: seed % NPA_EVERY === 0 ? "НПА" : "Новости",
    summary: excerptOf(item),
    impact: IMPACTS[(seed >>> 8) % IMPACTS.length],
    isPlaceholder: true,
  }
}
