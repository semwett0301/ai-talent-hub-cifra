import { createNpa, getNpa, listNpa, NpaApiError } from "@/api/npa"
import { DumaBillDialog } from "@/components/monitoring/DumaBillDialog"
import { SearchField } from "@/components/monitoring/Shared"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { ArticleChange, NpaItem, NpaVersion } from "@/types/monitoring"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ExternalLink,
  FileClock,
  FileText,
  History,
  Plus,
  RefreshCw,
  Scale,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react"
import { useMemo, useState } from "react"

const DETAIL_SKELETONS = [0, 1, 2]

export function NpaPage() {
  const registry = useNpaRegistry()
  const [query, setQuery] = useState("")
  const [selectedNpa, setSelectedNpa] = useState("")
  const [addOpen, setAddOpen] = useState(false)

  const visible = useVisibleNpa(registry.acts, query)
  const npaItem = visible.find((entry) => entry.id === selectedNpa) ?? visible[0]
  const details = useNpaDetails(npaItem?.id)

  return (
    <div className="content-columns npa-workspace">
      <RegistryPanel
        query={query}
        setQuery={setQuery}
        visible={visible}
        total={registry.acts.length}
        selectedNpa={npaItem?.id}
        setSelectedNpa={setSelectedNpa}
        loading={registry.loading}
        refreshing={registry.refreshing}
        error={registry.error}
        onRefresh={registry.refresh}
        onAdd={() => setAddOpen(true)}
      />
      <section className="panel details npa-details" aria-label="Подробности НПА">
        <NpaDetailPanel
          key={npaItem?.id ?? "empty"}
          item={details.item}
          loading={details.loading}
          error={details.error}
          onRetry={details.reload}
        />
      </section>
      <DumaBillDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        title="Добавить НПА для отслеживания"
        description="Вставьте ссылку на карточку законопроекта. Сервис загрузит актуальную Word-редакцию,
            сохранит первую версию и включит плановую проверку изменений."
        steps={["Проверка ссылки", "Загрузка редакции", "Добавление в реестр"]}
        submitLabel="Добавить в реестр"
        savingLabel="Загружаем карточку и официальный документ. Это может занять несколько секунд."
        onSubmit={async (url) => {
          const created = await registry.add(url)
          setQuery("")
          setSelectedNpa(created.id)
        }}
      />
    </div>
  )
}

function RegistryPanel(props: RegistryProps) {
  return (
    <section className="panel feed npa-registry">
      <div className="section-heading npa-heading">
        <div>
          <h2>Нормативные акты</h2>
          <p className="small muted">{props.visible.length} из {props.total}</p>
        </div>
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
      </div>
      <SearchField
        value={props.query}
        onChange={props.setQuery}
        placeholder="Поиск по названию и номеру"
      />
      <NpaList
        items={props.visible}
        selected={props.selectedNpa}
        onSelect={props.setSelectedNpa}
        loading={props.loading}
        error={props.error}
        onRetry={props.onRefresh}
      />
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
                {entry.initialSummaryStatus === "pending" && <small className="npa-update-mark">AI-описание готовится</small>}
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
  const initialSummary = item.summaryKind === "initial"
    ? item.summary
    : item.versions.find((version) => version.summaryKind === "initial")?.summary

  return (
    <>
      <dl className="npa-metadata">
        <div><dt>Текущая стадия</dt><dd>{item.stage ?? "Не определена"}</dd></div>
        <div><dt>Обновлено источником</dt><dd>{formatDateTime(item.sourceUpdatedAt)}</dd></div>
        <div><dt>Добавлено в реестр</dt><dd>{formatDate(item.createdAt)}</dd></div>
        <div><dt>Версий сохранено</dt><dd>{item.versions.length}</dd></div>
      </dl>
      <div className="summary-box">
        <h3><Sparkles />Описание законопроекта</h3>
        <p>{initialSummary ?? initialSummaryMessage(item.initialSummaryStatus)}</p>
        <small>Проверьте вывод по официальному документу перед юридически значимым решением.</small>
      </div>
      {item.summaryKind === "change" && (
        <div className="summary-box compact-summary">
          <h3><Sparkles />AI-резюме последнего изменения</h3>
          <p>{item.summary}</p>
        </div>
      )}
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
              <span>{version.summary ?? "AI-резюме пока не сформировано"}</span>
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
            <h3><Sparkles />{version.summaryKind === "initial" ? "AI-обзор законопроекта" : "Что изменилось"}</h3>
            <p>{version.summary ?? "AI-резюме пока не сформировано."}</p>
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
    refetchInterval: (query) => query.state.data?.initialSummaryStatus === "pending" ? 2_000 : false,
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

function useVisibleNpa(acts: NpaItem[], query: string) {
  return useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return acts
      .filter((entry) => `${entry.title} ${entry.billNumber ?? ""} ${entry.stage ?? ""}`.toLowerCase().includes(normalized))
      .sort((left, right) => Date.parse(right.sourceUpdatedAt ?? right.updatedAt) - Date.parse(left.sourceUpdatedAt ?? left.updatedAt))
  }, [acts, query])
}

function hasChanges(item: NpaItem) {
  return Boolean(item.summaryKind === "change" || item.articleChanges.length)
}

function initialSummaryMessage(status: NpaItem["initialSummaryStatus"]) {
  if (status === "pending") return "Пожалуйста, подождите: AI готовит краткое описание законопроекта."
  if (status === "failed") return "Описание пока не удалось подготовить. Сервис повторит обработку при следующем добавлении документа."
  return "Описание появится для НПА, добавленных после включения первичного AI-анализа."
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
  query: string
  setQuery: (value: string) => void
  visible: NpaItem[]
  total: number
  selectedNpa?: string
  setSelectedNpa: (id: string) => void
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
