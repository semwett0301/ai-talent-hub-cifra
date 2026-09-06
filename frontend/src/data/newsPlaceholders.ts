// Stand-ins for what the LLM stage will produce. The feed is live, but the AI summary and
// the "why it matters" note do not exist yet — so every item gets stable made-up values
// (seeded by its id, so a card never changes between renders) and the screen keeps its
// full layout. Replace with `analysis` fields when the pipeline lands.

import { excerptOf, type NewsOut } from "@/api/news"

export interface PlaceholderAnalysis {
  summary: string
  impact: string
  isPlaceholder: true
}

export type NewsItemView = NewsOut & PlaceholderAnalysis

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

export function withPlaceholders(item: NewsOut): NewsItemView {
  return {
    ...item,
    summary: excerptOf(item),
    impact: IMPACTS[seedOf(item.id) % IMPACTS.length],
    isPlaceholder: true,
  }
}
