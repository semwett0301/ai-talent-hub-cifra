import { useEffect, useMemo, useState } from "react"
import { EyeOff, ExternalLink, Pencil, RotateCcw, Sparkles } from "lucide-react"

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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { withPlaceholders, type NewsItemView } from "@/data/newsPlaceholders"
import { useSessionState } from "@/hooks/useSessionState"

// The feed's two tabs: the inbox, and the archive — what the reader hid (`visibility=dismissed`).
const TABS = ["Новости", "Архив"] as const
type Tab = (typeof TABS)[number]

const PAGE_SIZE = 200
const SEARCH_DEBOUNCE_MS = 300
const SKELETON_CARDS = [0, 1, 2, 3]

function useDebounced(value: string, delayMs: number): string {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}

function visibilityOf(tab: Tab): NewsVisibility {
  return tab === "Архив" ? "dismissed" : "visible"
}

export function NewsPage() {
  const [query, setQuery] = useState("")
  const [tab, setTab] = useState<Tab>("Новости")
  const [period, setPeriod] = useState(String(DEFAULT_PERIOD_HOURS))
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [edits, setEdits] = useSessionState<Record<string, string>>("news-edits", {})
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")
  const [notice, setNotice] = useState("")

  const search = useDebounced(query.trim(), SEARCH_DEBOUNCE_MS)
  const since = useMemo(() => sinceHoursAgo(Number(period)), [period])
  const feed = useNews({
    since,
    limit: PAGE_SIZE,
    visibility: visibilityOf(tab),
    ...(search ? { q: search } : {}),
  })
  const dismiss = useDismissNews()
  const restore = useRestoreNews()
  const reportError = useErrorToast()

  const items = useMemo(() => (feed.data?.items ?? []).map(withPlaceholders), [feed.data])
  const item = items.find((entry) => entry.id === selectedId) ?? items[0]

  function toggleHidden(selected: NewsItemView) {
    const isHidden = selected.dismissed_at !== null
    const mutation = isHidden ? restore : dismiss
    mutation.mutate(
      { params: { path: { news_id: selected.id } } },
      {
        onSuccess: () =>
          setNotice(isHidden ? "Материал возвращён из архива." : "Материал перенесён в архив."),
        onError: reportError,
      },
    )
  }

  function saveDraft() {
    if (item) setEdits({ ...edits, [item.id]: draft.trim() })
    setEditing(false)
    setNotice("Саммари обновлено")
  }

  return (
    <>
      <div className="content-columns">
        <section className="panel feed">
          <div className="section-heading">
            <h2>
              {tab === "Архив" ? "Архив" : "Входящие"} <span>{feed.data ? items.length : "…"}</span>
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
                onSelect={() => setSelectedId(entry.id)}
              />
            ))}
            {feed.data && !items.length && (
              <div className="empty-state">
                {tab === "Архив"
                  ? "В архиве пусто."
                  : "Материалы не найдены. Измените запрос или период."}
              </div>
            )}
          </div>
        </section>
        <section className="panel details" aria-label="Подробности новости">
          {item ? (
            <NewsDetails
              item={item}
              summary={edits[item.id] ?? item.summary}
              isEdited={item.id in edits}
              isBusy={dismiss.isPending || restore.isPending}
              onEdit={() => {
                setDraft(edits[item.id] ?? item.summary)
                setEditing(true)
              }}
              onToggleHidden={() => toggleHidden(item)}
            />
          ) : (
            <div className="empty-state">Выберите материал из ленты</div>
          )}
          <p role="status" className="notice">
            {notice}
          </p>
        </section>
      </div>
      <Dialog open={editing} onOpenChange={setEditing}>
        <DialogContent>
          <DialogTitle>Редактировать AI-саммари</DialogTitle>
          <DialogDescription>Правки сохраняются в текущей сессии браузера.</DialogDescription>
          <Textarea
            aria-label="Текст саммари"
            rows={7}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(false)}>
              Отмена
            </Button>
            <Button disabled={!draft.trim()} onClick={saveDraft}>
              Сохранить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function NewsDetails({
  item,
  summary,
  isEdited,
  isBusy,
  onEdit,
  onToggleHidden,
}: {
  item: NewsItemView
  summary: string
  isEdited: boolean
  isBusy: boolean
  onEdit: () => void
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
        <p>{summary}</p>
        {isEdited && <small>Отредактировано вручную</small>}
        {!isEdited && item.isPlaceholder && <small>Заглушка: анализ ещё не подключён</small>}
      </div>
      <div className="impact-box">
        <h3>Почему это важно для GS Labs</h3>
        <p>{item.impact}</p>
      </div>
      <div className="actions">
        <Button variant="outline" onClick={onEdit}>
          <Pencil />
          Редактировать
        </Button>
        {isHidden ? (
          <Button variant="default" disabled={isBusy} onClick={onToggleHidden}>
            <RotateCcw />
            Вернуть из архива
          </Button>
        ) : (
          <Button variant="destructive" disabled={isBusy} onClick={onToggleHidden}>
            <EyeOff />
            В архив
          </Button>
        )}
      </div>
    </>
  )
}

function NewsCard({
  item,
  selected,
  onSelect,
}: {
  item: NewsItemView
  selected: boolean
  onSelect: () => void
}) {
  return (
    <Button
      variant="ghost"
      className={`news-card ${selected ? "selected" : ""}`}
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
  )
}
