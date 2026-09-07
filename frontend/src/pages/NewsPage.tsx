import { useEffect, useMemo, useState } from "react"
import { EyeOff, ExternalLink, Plus, RotateCcw, Sparkles } from "lucide-react"

import { errorMessage, errorStatus } from "@/api/client"
import { useErrorToast } from "@/api/errorToast"
import {
  DEFAULT_PERIOD_HOURS,
  PERIODS,
  RELEVANCE_TONES,
  excerptOf,
  formatMoment,
  formatToday,
  newsMoment,
  sinceHoursAgo,
} from "@/api/news"
import type { NewsOut, NewsRelevance, NewsVisibility } from "@/api/news"
import { useDismissNews, useEscalateNpa, useNews, useRestoreNews } from "@/api/newsMutations"
import { npaErrorMessage } from "@/api/npa"
import { RELIABILITY_LABELS } from "@/api/sources"
import { DumaBillDialog } from "@/components/monitoring/DumaBillDialog"
import { Choice, SearchField } from "@/components/monitoring/Shared"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

// The feed's tabs: the current items, what the reader hid (`visibility=dismissed`), and
// items flagged as NPA-relevant (`is_alert`) — a reader attaches the actual law from here.
const TABS = ["Актуальные", "Скрытые", "Алерты"] as const
type Tab = (typeof TABS)[number]

const SEARCH_DEBOUNCE_MS = 300
const SKELETON_CARDS = [0, 1, 2, 3]
// The `@keyframes` name in App.css a hidden / restored card plays before it leaves the list.
const LEAVE_ANIMATION = "news-card-leave"
// What the details say while the pipeline has not reached the item yet.
const SUMMARY_PENDING = "AI-саммари ещё не готово — материал в обработке."

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

/** The card's stripe / badge modifier: the category's tone, or `pending` before ranking. */
function toneOf(item: NewsOut): string {
  return item.relevance ? RELEVANCE_TONES[item.relevance.category] : "pending"
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
    ...(tab === "Алерты" ? { is_alert: true } : {}),
    ...(search ? { q: search } : {}),
  })
  const dismiss = useDismissNews()
  const restore = useRestoreNews()
  const reportError = useErrorToast()

  const items = feed.data ?? []
  const item = items.find((entry) => entry.id === selectedId) ?? items[0]

  // Runs when the leave animation ends: the swipe is done, now the server does its part. The
  // card stays played-out until the mutation settles — that is, until the refetched list landed.
  function toggleHidden(selected: NewsOut) {
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
              {tab === "Скрытые" && "Скрытых материалов нет."}
              {tab === "Алерты" && "Сигналов о НПА нет."}
              {tab === "Актуальные" && "Материалы не найдены. Измените запрос или период."}
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
  item: NewsOut
  isBusy: boolean
  onToggleHidden: () => void
}) {
  const isHidden = item.dismissed_at !== null
  const [lawDialogOpen, setLawDialogOpen] = useState(false)
  const escalate = useEscalateNpa()

  return (
    <>
      <div className="detail-meta">
        <span>{formatMoment(newsMoment(item))}</span>
        {item.relevance && <RelevanceBadge relevance={item.relevance} />}
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
        <p>{item.summary ?? SUMMARY_PENDING}</p>
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
        {item.is_alert && (
          <Button variant="outline" onClick={() => setLawDialogOpen(true)}>
            <Plus />
            Добавить закон вручную
          </Button>
        )}
      </div>
      <DumaBillDialog
        open={lawDialogOpen}
        onOpenChange={setLawDialogOpen}
        title="Добавить закон вручную"
        description="Вставьте ссылку на карточку законопроекта в Государственной Думе. Сервис
            зарегистрирует акт в npa_service и свяжет его с этой новостью."
        submitLabel="Добавить закон"
        savingLabel="Регистрируем закон в npa_service. Это может занять несколько секунд."
        onSubmit={async (url) => {
          try {
            await escalate.mutateAsync({
              params: { path: { news_id: item.id } },
              body: { url, title: item.title, text: item.text, published_at: item.published_at },
            })
          } catch (cause) {
            const status = errorStatus(cause)
            throw new Error(status ? npaErrorMessage(status) : "Сервис НПА недоступен", { cause })
          }
        }}
      />
    </>
  )
}

/** The category alone — the score and the model's reasons stay server-side. */
function RelevanceBadge({ relevance }: { relevance: NewsRelevance }) {
  return (
    <Badge className={`status ${RELEVANCE_TONES[relevance.category]}`} title="AI-приоритет">
      {relevance.category}
    </Badge>
  )
}

function NewsCard({
  item,
  selected,
  isLeaving,
  onSelect,
  onLeft,
}: {
  item: NewsOut
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
        className={`news-card ${toneOf(item)} ${selected ? "selected" : ""}`}
        aria-pressed={selected}
        onClick={onSelect}
      >
        <span className="card-meta">
          <span>
            {item.source_name} · {formatMoment(newsMoment(item))}
          </span>
          {item.relevance && <RelevanceBadge relevance={item.relevance} />}
        </span>
        <strong>{item.title}</strong>
        <span className="excerpt">{excerptOf(item)}</span>
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
