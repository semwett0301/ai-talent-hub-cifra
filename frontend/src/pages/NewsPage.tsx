import { useEffect, useMemo, useState } from "react"
import { EyeOff, ExternalLink, RotateCcw, Sparkles } from "lucide-react"

import { errorMessage } from "@/api/client"
import { useErrorToast } from "@/api/errorToast"
import {
  DEFAULT_PERIOD_HOURS,
  PERIODS,
  excerptOf,
  formatMoment,
  formatToday,
  newsMoment,
  sinceHoursAgo,
} from "@/api/news"
import type { NewsOut, NewsVisibility } from "@/api/news"
import { useDismissNews, useNews, useRestoreNews } from "@/api/newsMutations"
import { RELIABILITY_LABELS } from "@/api/sources"
import { Choice, SearchField } from "@/components/monitoring/Shared"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { withPlaceholders, type NewsItemView } from "@/data/newsPlaceholders"

// The feed's two tabs: the current items, and what the reader hid (`visibility=dismissed`).
const TABS = ["Актуальные", "Скрытые"] as const
type Tab = (typeof TABS)[number]

const SEARCH_DEBOUNCE_MS = 300
const SKELETON_CARDS = [0, 1, 2, 3]
// The `@keyframes` name in App.css a hidden / restored card plays before it leaves the list.
const LEAVE_ANIMATION = "news-card-leave"

function useDebounced(value: string, delayMs: number): string {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}

function visibilityOf(tab: Tab): NewsVisibility {
  return tab === "Скрытые" ? "dismissed" : "visible"
}

export function NewsPage() {
  const [query, setQuery] = useState("")
  const [tab, setTab] = useState<Tab>("Актуальные")
  const [period, setPeriod] = useState(String(DEFAULT_PERIOD_HOURS))
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [leavingId, setLeavingId] = useState<string | null>(null)

  const search = useDebounced(query.trim(), SEARCH_DEBOUNCE_MS)
  const since = useMemo(() => sinceHoursAgo(Number(period)), [period])
  const feed = useNews({
    since,
    visibility: visibilityOf(tab),
    ...(search ? { q: search } : {}),
  })
  const dismiss = useDismissNews()
  const restore = useRestoreNews()
  const reportError = useErrorToast()

  const items = useMemo(() => (feed.data ?? []).map(withPlaceholders), [feed.data])
  const item = items.find((entry) => entry.id === selectedId) ?? items[0]

  // Runs when the leave animation ends: the swipe is done, now the server does its part. The
  // card stays played-out until the mutation settles — that is, until the refetched list landed.
  function toggleHidden(selected: NewsItemView) {
    const mutation = selected.dismissed_at !== null ? restore : dismiss
    mutation.mutate(
      { params: { path: { news_id: selected.id } } },
      { onError: reportError, onSettled: () => setLeavingId(null) },
    )
  }

  return (
    <div className="content-columns">
      <section className="panel feed">
        <div className="section-heading">
          <h2>
            {tab} <span>{feed.data ? items.length : "…"}</span>
          </h2>
          <span className="small muted">{formatToday()}</span>
        </div>
        <SearchField
          value={query}
          onChange={setQuery}
          placeholder="Поиск по заголовку и тексту"
        />
        <div className="filters">
          {TABS.map((label) => (
            <Button
              key={label}
              size="sm"
              variant="outline"
              aria-pressed={tab === label}
              className={tab === label ? "active-filter" : ""}
              onClick={() => setTab(label)}
            >
              {label}
            </Button>
          ))}
          <Choice
            label="Период новостей"
            value={period}
            onChange={setPeriod}
            options={PERIODS.map(({ hours, label }) => ({ value: String(hours), label }))}
          />
        </div>
        <div className="news-list">
          {feed.isPending &&
            SKELETON_CARDS.map((card) => <Skeleton key={card} className="source-skeleton" />)}
          {feed.error && (
            <p role="alert" className="form-error">
              {errorMessage(feed.error)}
            </p>
          )}
          {items.map((entry) => (
            <NewsCard
              key={entry.id}
              item={entry}
              selected={entry.id === item?.id}
              isLeaving={entry.id === leavingId}
              onSelect={() => setSelectedId(entry.id)}
              onLeft={() => toggleHidden(entry)}
            />
          ))}
          {feed.data && !items.length && (
            <div className="empty-state">
              {tab === "Скрытые"
                ? "Скрытых материалов нет."
                : "Материалы не найдены. Измените запрос или период."}
            </div>
          )}
        </div>
      </section>
      <section className="panel details" aria-label="Подробности новости">
        {item ? (
          <NewsDetails
            item={item}
            isBusy={leavingId !== null}
            onToggleHidden={() => setLeavingId(item.id)}
          />
        ) : (
          <div className="empty-state">Выберите материал из ленты</div>
        )}
      </section>
    </div>
  )
}

function NewsDetails({
  item,
  isBusy,
  onToggleHidden,
}: {
  item: NewsItemView
  isBusy: boolean
  onToggleHidden: () => void
}) {
  const isHidden = item.dismissed_at !== null

  return (
    <>
      <div className="detail-meta">
        <span>{formatMoment(newsMoment(item))}</span>
      </div>
      <a className="detail-title" href={item.url} target="_blank" rel="noopener noreferrer">
        <h2>{item.title}</h2>
        <span className="detail-title-hint">
          <ExternalLink size={13} />
          Открыть оригинал
        </span>
      </a>
      <div className="detail-source">
        <span className="detail-source-name">{item.source_name}</span>
        <Badge className={`reliability ${item.source_reliability}`} title="Приоритет источника">
          {RELIABILITY_LABELS[item.source_reliability]}
        </Badge>
      </div>
      <div className="summary-box">
        <h3>
          <Sparkles />
          AI-САММАРИ
        </h3>
        <p>{item.summary}</p>
        {item.isPlaceholder && <small>Заглушка: анализ ещё не подключён</small>}
      </div>
      <div className="impact-box">
        <h3>Почему это важно для GS Labs</h3>
        <p>{item.impact}</p>
      </div>
      <div className="actions">
        {isHidden ? (
          <Button variant="default" disabled={isBusy} onClick={onToggleHidden}>
            <RotateCcw />
            Вернуть
          </Button>
        ) : (
          <Button variant="destructive" disabled={isBusy} onClick={onToggleHidden}>
            <EyeOff />
            Скрыть
          </Button>
        )}
      </div>
    </>
  )
}

function NewsCard({
  item,
  selected,
  isLeaving,
  onSelect,
  onLeft,
}: {
  item: NewsItemView
  selected: boolean
  isLeaving: boolean
  onSelect: () => void
  onLeft: () => void
}) {
  return (
    <div
      className={isLeaving ? "news-slot leaving" : "news-slot"}
      onAnimationEnd={(event) => {
        if (event.animationName === LEAVE_ANIMATION) onLeft()
      }}
    >
      <Button
        variant="ghost"
        className={selected ? "news-card selected" : "news-card"}
        aria-pressed={selected}
        onClick={onSelect}
      >
        <span className="card-meta">
          <span>
            {item.source_name} · {formatMoment(newsMoment(item))}
          </span>
        </span>
        <strong>{item.title}</strong>
        <span className="excerpt">{excerptOf(item satisfies NewsOut)}</span>
        {item.source_tags.length > 0 && (
          <span className="tags">
            {item.source_tags.map((tag) => (
              <Badge variant="secondary" key={tag}>
                {tag}
              </Badge>
            ))}
          </span>
        )}
      </Button>
    </div>
  )
}
