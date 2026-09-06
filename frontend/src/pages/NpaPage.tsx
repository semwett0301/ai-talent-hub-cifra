import { createNpa, getNpa, listNpa, NpaApiError } from "@/api/npa"
import { SearchField } from "@/components/monitoring/Shared"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { news } from "@/data/news"
import type { ArticleChange, NewsItem, NpaItem, NpaVersion } from "@/types/monitoring"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ExternalLink,
  FileClock,
  FileText,
  History,
  LoaderCircle,
  Plus,
  RefreshCw,
  Scale,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react"
import { useMemo, useState } from "react"

type NpaFilter = "Реестр отслеживаемых НПА" | "Алерты" | "Обновления НПА"
const FILTERS: NpaFilter[] = ["Реестр отслеживаемых НПА", "Алерты", "Обновления НПА"]
const DETAIL_SKELETONS = [0, 1, 2]

export function NpaPage() {
  const registry = useNpaRegistry()
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState<NpaFilter>(FILTERS[0])
  const [selectedNpa, setSelectedNpa] = useState("")
  const [selectedAlert, setSelectedAlert] = useState(news[0]?.id ?? "")
  const [addOpen, setAddOpen] = useState(false)

  const visible = useVisibleNpa(registry.acts, query, filter)
  const alerts = useAlerts(query)
  const npaItem = visible.find((entry) => entry.id === selectedNpa) ?? visible[0]
  const alertItem = alerts.find((entry) => entry.id === selectedAlert) ?? alerts[0]
  const details = useNpaDetails(filter === "Алерты" ? undefined : npaItem?.id)

  return (
    <div className="content-columns npa-workspace">
      <RegistryPanel
        filter={filter}
        setFilter={setFilter}
        query={query}
        setQuery={setQuery}
        visible={visible}
        total={registry.acts.length}
        alerts={alerts}
        selectedNpa={npaItem?.id}
        selectedAlert={alertItem?.id}
        setSelectedNpa={setSelectedNpa}
        setSelectedAlert={setSelectedAlert}
        loading={registry.loading}
        refreshing={registry.refreshing}
        error={registry.error}
        onRefresh={registry.refresh}
        onAdd={() => setAddOpen(true)}
      />
      <section className="panel details npa-details" aria-label="Подробности НПА">
        {filter === "Алерты" ? (
          <AlertDetails item={alertItem} onAdd={() => setAddOpen(true)} />
        ) : (
          <NpaDetailPanel
            key={npaItem?.id ?? "empty"}
            item={details.item}
            loading={details.loading}
            error={details.error}
            onRetry={details.reload}
          />
        )}
      </section>
      <LawDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onAdd={async (url) => {
          const created = await registry.add(url)
          setFilter(FILTERS[0])
          setQuery("")
          setSelectedNpa(created.id)
        }}
      />
    </div>
  )
}

function RegistryPanel(props: RegistryProps) {
  const isAlerts = props.filter === "Алерты"
  const countLabel = isAlerts
    ? `${props.alerts.length} сигналов`
    : `${props.visible.length} из ${props.total}`

  return (
    <section className="panel feed npa-registry">
      <div className="section-heading npa-heading">
        <div>
          <h2>Нормативные акты</h2>
          <p className="small muted">{countLabel}</p>
        </div>
        {!isAlerts && (
          <Button
            variant="outline"
            size="icon"
            aria-label="Обновить реестр"
            title="Обновить реестр"
            disabled={props.refreshing}
            onClick={props.onRefresh}
          >
            <RefreshCw className={props.refreshing ? "spin" : ""} />
          </Button>
        )}
      </div>
      <div className="filters npa-filters">
        {FILTERS.map((label) => (
          <Button
            key={label}
            variant="outline"
            size="sm"
            aria-pressed={props.filter === label}
            className={props.filter === label ? "active-filter" : ""}
            onClick={() => props.setFilter(label)}
          >
            {label}
          </Button>
        ))}
      </div>
      <SearchField
        value={props.query}
        onChange={props.setQuery}
        placeholder={isAlerts ? "Поиск по новостям и регуляторам" : "Поиск по названию и номеру"}
      />
      {isAlerts ? (
        <AlertList items={props.alerts} selected={props.selectedAlert} onSelect={props.setSelectedAlert} />
      ) : (
        <NpaList
          items={props.visible}
          selected={props.selectedNpa}
          onSelect={props.setSelectedNpa}
          loading={props.loading}
          error={props.error}
          onRetry={props.onRefresh}
        />
      )}
      <div className="sticky-add-law">
        <Button variant="outline" className="add-source" onClick={props.onAdd}>
          <Plus />
          Добавить НПА для отслеживания
        </Button>
      </div>
    </section>
  )
}

function NpaList({ items, selected, onSelect, loading, error, onRetry }: NpaListProps) {
  if (loading) {
    return <div className="npa-list" aria-label="Загрузка реестра">
      {[0, 1, 2].map((row) => <Skeleton key={row} className="npa-card-skeleton" />)}
    </div>
  }

  if (error) {
    return <div className="empty-state npa-error-state" role="alert">
      <p>{error}</p>
      <Button variant="outline" size="sm" onClick={onRetry}><RefreshCw />Повторить</Button>
    </div>
  }

  return (
    <>
      <div className="npa-list-header"><span>ДОКУМЕНТ</span><span>СТАТУС</span><span>ПРОВЕРЕНО</span></div>
      <div className="npa-list">
        {items.map((entry) => (
          <Button
            variant="ghost"
            key={entry.id}
            className={`npa-card ${entry.id === selected ? "selected" : ""}`}
            onClick={() => onSelect(entry.id)}
          >
            <span className="npa-grid">
              <span>
                <strong>{entry.title}</strong>
                <small>Законопроект № {entry.billNumber ?? "не указан"}</small>
              </span>
              <span>
                <Badge className={`status ${statusTone(entry.trackingStatus)}`}>
                  {statusLabel(entry.trackingStatus)}
                </Badge>
                <small>{entry.stage ?? "Стадия не определена"}</small>
              </span>
              <span className="npa-checked">
                {formatDate(entry.lastCheckedAt)}
                {hasChanges(entry) && <small className="npa-update-mark">Есть изменения</small>}
              </span>
            </span>
          </Button>
        ))}
        {!items.length && <p className="empty-state">По вашему запросу ничего не найдено.</p>}
      </div>
    </>
  )
}

function NpaDetailPanel({ item, loading, error, onRetry }: NpaDetailPanelProps) {
  const [selectedVersion, setSelectedVersion] = useState<NpaVersion | null>(null)

  if (loading) {
    return <div className="npa-detail-loading" aria-label="Загрузка карточки НПА">
      {DETAIL_SKELETONS.map((row) => <Skeleton key={row} className={`npa-detail-skeleton row-${row}`} />)}
    </div>
  }
  if (error) {
    return <div className="empty-state npa-error-state" role="alert">
      <p>{error}</p>
      <Button variant="outline" size="sm" onClick={onRetry}><RefreshCw />Повторить</Button>
    </div>
  }
  if (!item) return <p className="empty-state">Выберите документ из реестра.</p>

  return (
    <>
      <div className="detail-meta">
        <Badge className={`status ${statusTone(item.trackingStatus)}`}>
          {item.trackingStatus === "tracking" ? <CalendarClock /> : <CheckCircle2 />}
          {statusLabel(item.trackingStatus)}
        </Badge>
        <span>Последняя проверка: {formatDateTime(item.lastCheckedAt)}</span>
      </div>
      <h2>{item.title}</h2>
      <p className="small muted">Законопроект № {item.billNumber ?? "не указан"} · Государственная Дума</p>
      <div className="npa-primary-links">
        <a className="npa-source-link" href={item.url} target="_blank" rel="noreferrer">
          Карточка законопроекта <ExternalLink />
        </a>
        {item.documentUrl && (
          <a className="npa-source-link" href={item.documentUrl} target="_blank" rel="noreferrer">
            Текущая редакция <FileText />
          </a>
        )}
      </div>

      <Tabs defaultValue="overview" className="detail-tabs">
        <TabsList>
          <TabsTrigger value="overview"><Scale />Обзор</TabsTrigger>
          <TabsTrigger value="changes"><FileText />Изменения ({item.articleChanges.length})</TabsTrigger>
          <TabsTrigger value="history"><History />Версии ({item.versions.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <NpaOverview item={item} />
        </TabsContent>
        <TabsContent value="changes">
          <div className="npa-tab-copy">
            <h3>Изменения последней редакции</h3>
            <p className="small muted">Сравнение сформировано по текстам двух последовательных версий.</p>
          </div>
          <ArticleChanges changes={item.articleChanges} />
        </TabsContent>
        <TabsContent value="history">
          <VersionHistory versions={item.versions} onSelect={setSelectedVersion} />
        </TabsContent>
      </Tabs>
      <VersionDialog version={selectedVersion} onClose={() => setSelectedVersion(null)} />
    </>
  )
}

function NpaOverview({ item }: { item: NpaItem }) {
  return (
    <>
      <dl className="npa-metadata">
        <div><dt>Текущая стадия</dt><dd>{item.stage ?? "Не определена"}</dd></div>
        <div><dt>Обновлено источником</dt><dd>{formatDateTime(item.sourceUpdatedAt)}</dd></div>
        <div><dt>Добавлено в реестр</dt><dd>{formatDate(item.createdAt)}</dd></div>
        <div><dt>Версий сохранено</dt><dd>{item.versions.length}</dd></div>
      </dl>
      <div className="summary-box">
        <h3><Sparkles />AI-резюме последнего изменения</h3>
        <p>{item.summary ?? "Это первая сохранённая версия. Изменений относительно предыдущей редакции пока нет."}</p>
        <small>Проверьте вывод по официальному документу перед юридически значимым решением.</small>
      </div>
      <div className="npa-monitor-note">
        <ShieldCheck />
        <div>
          <strong>{item.trackingStatus === "tracking" ? "Автоматическая проверка включена" : "Автоматическая проверка завершена"}</strong>
          <p>{monitoringDescription(item)}</p>
        </div>
      </div>
    </>
  )
}

function ArticleChanges({ changes }: { changes: ArticleChange[] }) {
  const [opened, setOpened] = useState<number | null>(changes.length === 1 ? 0 : null)
  if (!changes.length) {
    return <div className="empty-state npa-empty-changes">
      <FileText />
      <p>В последней сохранённой версии содержательных изменений не найдено.</p>
    </div>
  }

  return (
    <section className="article-changes">
      <ul>
        {changes.map((change, index) => (
          <li key={`${change.article}-${index}`}>
            <Button variant="ghost" onClick={() => setOpened(opened === index ? null : index)}>
              <span><strong>{change.article}</strong><small>{change.summary}</small></span>
              {opened === index ? <X /> : <Plus />}
            </Button>
            {opened === index && <ChangeDiff change={change} />}
          </li>
        ))}
      </ul>
    </section>
  )
}

function ChangeDiff({ change }: { change: ArticleChange }) {
  return (
    <div className="npa-diff">
      <div className="diff-head"><span>Было</span><span>Стало</span></div>
      <div className="diff-row">
        <p>{change.before || "Фрагмент отсутствовал"}</p>
        <ArrowRight aria-hidden="true" />
        <p>{change.after || "Фрагмент удалён"}</p>
      </div>
    </div>
  )
}

function VersionHistory({ versions, onSelect }: { versions: NpaVersion[]; onSelect: (version: NpaVersion) => void }) {
  if (!versions.length) return <p className="empty-state">История версий пока пуста.</p>
  return (
    <ol className="version-history">
      {versions.map((version, index) => (
        <li key={version.id}>
          <Button variant="ghost" onClick={() => onSelect(version)}>
            <span className="version-marker"><FileClock /></span>
            <span>
              <strong>{index === 0 ? "Текущая версия" : `Версия ${versions.length - index}`}</strong>
              <small>{version.stage} · {formatDateTime(version.sourceUpdatedAt)}</small>
              <span>{version.summary ?? "Первая сохранённая редакция"}</span>
            </span>
            <ArrowRight />
          </Button>
        </li>
      ))}
    </ol>
  )
}

function VersionDialog({ version, onClose }: { version: NpaVersion | null; onClose: () => void }) {
  return (
    <Dialog open={Boolean(version)} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="npa-version-dialog">
        {version && <>
          <DialogTitle>{version.stage}</DialogTitle>
          <DialogDescription>
            Редакция источника от {formatDateTime(version.sourceUpdatedAt)}
          </DialogDescription>
          <div className="version-dialog-links">
            <a className="npa-source-link" href={version.documentUrl} target="_blank" rel="noreferrer">
              Открыть официальный документ <ExternalLink />
            </a>
          </div>
          <div className="summary-box compact-summary">
            <h3><Sparkles />Что изменилось</h3>
            <p>{version.summary ?? "Это первая сохранённая редакция документа."}</p>
          </div>
          <div className="version-dialog-changes">
            <h3>Изменения по статьям</h3>
            <ArticleChanges changes={version.articleChanges} />
          </div>
        </>}
      </DialogContent>
    </Dialog>
  )
}

// News-to-NPA alerts are intentionally left on their existing implementation path.
function AlertList({ items, selected, onSelect }: AlertListProps) {
  return <div className="npa-list">{items.map((entry) => <Button variant="ghost" key={entry.id}
    className={`news-card ${entry.priority} ${entry.id === selected ? "selected" : ""}`}
    onClick={() => onSelect(entry.id)}><span className="card-meta"><span>{entry.source} · {entry.time}</span>
      <span>Сигнал о НПА</span></span><strong>{entry.title}</strong>
      <span className="excerpt">{entry.excerpt}</span></Button>)}</div>
}

function AlertDetails({ item, onAdd }: { item?: NewsItem; onAdd: () => void }) {
  if (!item) return <p className="empty-state">Выберите новость</p>
  return <><div className="detail-meta"><Badge className={`status ${item.priority}`}>
    • Сигнал о НПА</Badge><span>{item.time}</span></div><h2>{item.title}</h2>
    <p className="small muted">{item.source} · новость</p><div className="summary-box">
      <h3><Sparkles />AI-САММАРИ</h3><p>{item.summary}</p></div>
    <Button className="manual-law-button" onClick={onAdd}><Plus />Добавить закон вручную</Button></>
}

function LawDialog({ open, onOpenChange, onAdd }: LawDialogProps) {
  const [url, setUrl] = useState("")
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  function changeOpen(nextOpen: boolean) {
    if (!nextOpen && saving) return
    if (!nextOpen) {
      setUrl("")
      setError("")
    }
    onOpenChange(nextOpen)
  }

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault()
    if (!isDumaBillUrl(url)) {
      setError("Нужна ссылка вида https://sozd.duma.gov.ru/bill/123-8")
      return
    }
    setSaving(true)
    setError("")
    try {
      await onAdd(url.trim())
      setUrl("")
      setError("")
      onOpenChange(false)
    } catch (cause) {
      setError(cause instanceof NpaApiError ? cause.message : "Не удалось добавить НПА")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogContent>
        <form className="npa-add-form" onSubmit={handleAdd}>
          <DialogTitle>Добавить НПА для отслеживания</DialogTitle>
          <DialogDescription>
            Вставьте ссылку на карточку законопроекта. Сервис загрузит актуальную Word-редакцию,
            сохранит первую версию и включит плановую проверку изменений.
          </DialogDescription>
          <div className="npa-add-steps" aria-label="Что произойдёт после добавления">
            <span><strong>1</strong>Проверка ссылки</span>
            <span><strong>2</strong>Загрузка редакции</span>
            <span><strong>3</strong>Добавление в реестр</span>
          </div>
          <label className="form-field">
            Ссылка на законопроект
            <Input
              autoFocus
              aria-label="Ссылка на законопроект"
              aria-invalid={Boolean(error)}
              value={url}
              onChange={(event) => { setUrl(event.target.value); setError("") }}
              placeholder="https://sozd.duma.gov.ru/bill/1286425-8"
            />
          </label>
          {error && <p role="alert" className="form-error">{error}</p>}
          {saving && <p className="small muted npa-saving-note" aria-live="polite">
            <LoaderCircle className="spin" /> Загружаем карточку и официальный документ. Это может занять несколько секунд.
          </p>}
          <DialogFooter>
            <Button type="button" variant="outline" disabled={saving} onClick={() => changeOpen(false)}>Отмена</Button>
            <Button type="submit" disabled={!url.trim() || saving}>
              {saving ? <LoaderCircle className="spin" /> : <Scale />}
              {saving ? "Добавляем…" : "Добавить в реестр"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function useNpaRegistry() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ["npa", "list"],
    queryFn: ({ signal }) => listNpa(signal),
  })

  const add = async (url: string) => {
    const created = await createNpa(url)
    queryClient.setQueryData<NpaItem[]>(["npa", "list"], (current = []) => [
      created,
      ...current.filter((entry) => entry.id !== created.id),
    ])
    queryClient.setQueryData(["npa", "detail", created.id], created)
    return created
  }

  const cause = query.error
  const error = cause
    ? cause instanceof NpaApiError ? cause.message : "Сервис НПА недоступен"
    : ""

  return {
    acts: query.data ?? [],
    loading: query.isPending,
    refreshing: query.isFetching,
    error,
    refresh: () => { void queryClient.invalidateQueries({ queryKey: ["npa"] }) },
    add,
  }
}

function useNpaDetails(id: string | undefined) {
  const query = useQuery({
    queryKey: ["npa", "detail", id],
    queryFn: ({ signal }) => getNpa(id!, signal),
    enabled: Boolean(id),
  })
  const cause = query.error
  const error = cause
    ? cause instanceof NpaApiError ? cause.message : "Не удалось загрузить карточку НПА"
    : ""

  return {
    item: id ? query.data : undefined,
    loading: Boolean(id) && query.isPending,
    error,
    reload: () => { void query.refetch() },
  }
}

function useVisibleNpa(acts: NpaItem[], query: string, filter: NpaFilter) {
  return useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return acts
      .filter((entry) => `${entry.title} ${entry.billNumber ?? ""} ${entry.stage ?? ""}`.toLowerCase().includes(normalized))
      .filter((entry) => filter !== "Обновления НПА" || hasChanges(entry))
      .sort((left, right) => Date.parse(right.sourceUpdatedAt ?? right.updatedAt) - Date.parse(left.sourceUpdatedAt ?? left.updatedAt))
  }, [acts, query, filter])
}

function useAlerts(query: string) {
  return useMemo(() => news.filter((entry) => entry.kind === "НПА")
    .filter((entry) => `${entry.title} ${entry.source}`.toLowerCase().includes(query.toLowerCase()))
    .sort((left, right) => right.relevance - left.relevance), [query])
}

function hasChanges(item: NpaItem) {
  return Boolean(item.summary || item.articleChanges.length)
}

function statusLabel(status: NpaItem["trackingStatus"]) {
  if (status === "tracking") return "На контроле"
  if (status === "published") return "Опубликован"
  return "Без мониторинга"
}

function statusTone(status: NpaItem["trackingStatus"]) {
  if (status === "tracking") return "normal"
  if (status === "published") return "published"
  return "unsupported"
}

function monitoringDescription(item: NpaItem) {
  if (item.trackingStatus === "tracking") {
    return "Сервис проверяет карточку Госдумы по расписанию и сохраняет новую версию при изменении текста."
  }
  if (item.trackingStatus === "published") {
    return `Закон опубликован${item.publishedAt ? ` ${formatDate(item.publishedAt)}` : ""}. История версий сохранена.`
  }
  return "Автоматический контроль недоступен для этой записи. Официальная карточка остаётся доступна по ссылке."
}

function isDumaBillUrl(value: string) {
  try {
    const url = new URL(value.trim())
    return url.protocol === "https:" && url.hostname === "sozd.duma.gov.ru" &&
      /^\/bill\/\d+-\d+\/?$/.test(url.pathname) && !url.search && !url.hash
  } catch {
    return false
  }
}

function formatDate(value: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat("ru-RU").format(date)
}

function formatDateTime(value: string | null) {
  if (!value) return "ещё не выполнялась"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date)
}

interface RegistryProps {
  filter: NpaFilter
  setFilter: (value: NpaFilter) => void
  query: string
  setQuery: (value: string) => void
  visible: NpaItem[]
  total: number
  alerts: NewsItem[]
  selectedNpa?: string
  selectedAlert?: string
  setSelectedNpa: (id: string) => void
  setSelectedAlert: (id: string) => void
  loading: boolean
  refreshing: boolean
  error: string
  onRefresh: () => void
  onAdd: () => void
}

interface NpaListProps {
  items: NpaItem[]
  selected?: string
  onSelect: (id: string) => void
  loading: boolean
  error: string
  onRetry: () => void
}

interface NpaDetailPanelProps {
  item?: NpaItem
  loading: boolean
  error: string
  onRetry: () => void
}

interface AlertListProps {
  items: NewsItem[]
  selected?: string
  onSelect: (id: string) => void
}

interface LawDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (url: string) => Promise<void>
}
