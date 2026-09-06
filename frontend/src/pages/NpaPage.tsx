import { createNpa, listNpa, NpaApiError } from "@/api/npa";
import { SearchField } from "@/components/monitoring/Shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { news } from "@/data/news";
import type { NewsItem, NpaItem } from "@/types/monitoring";
import { ExternalLink, LoaderCircle, Plus, Scale, ShieldCheck, Sparkles, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type NpaFilter = "Реестр отслеживаемых НПА" | "Алерты" | "Обновления НПА";
const FILTERS: NpaFilter[] = ["Реестр отслеживаемых НПА", "Алерты", "Обновления НПА"];

export function NpaPage() {
  const registry = useNpaRegistry();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<NpaFilter>(FILTERS[0]);
  const [selectedNpa, setSelectedNpa] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(news[0]?.id ?? "");
  const [addOpen, setAddOpen] = useState(false);

  const visible = useVisibleNpa(registry.acts, query, filter);
  const alerts = useAlerts(query);
  const npaItem = visible.find((entry) => entry.id === selectedNpa) ?? visible[0];
  const alertItem = alerts.find((entry) => entry.id === selectedAlert) ?? alerts[0];

  return <div className="content-columns npa-workspace">
    <RegistryPanel filter={filter} setFilter={setFilter} query={query} setQuery={setQuery}
      visible={visible} alerts={alerts} selectedNpa={npaItem?.id} selectedAlert={alertItem?.id}
      setSelectedNpa={setSelectedNpa} setSelectedAlert={setSelectedAlert}
      loading={registry.loading} error={registry.error} onAdd={() => setAddOpen(true)} />
    <section className="panel details" aria-label="Подробности НПА">
      {filter === "Алерты"
        ? <AlertDetails item={alertItem} onAdd={() => setAddOpen(true)} />
        : <NpaDetails item={npaItem} />}
    </section>
    <LawDialog open={addOpen} onOpenChange={setAddOpen} onAdd={async (url) => {
      const created = await registry.add(url); setSelectedNpa(created.id);
    }} />
  </div>;
}

function RegistryPanel(props: RegistryProps) {
  const isAlerts = props.filter === "Алерты";
  return <section className="panel feed npa-registry">
    <h2>НПА</h2>
    <div className="filters">{FILTERS.map((label) => <Button key={label} variant="outline"
      size="sm" aria-pressed={props.filter === label}
      className={props.filter === label ? "active-filter" : ""}
      onClick={() => props.setFilter(label)}>{label}</Button>)}</div>
    <SearchField value={props.query} onChange={props.setQuery}
      placeholder={isAlerts ? "Поиск по новостям и регуляторам" : "Поиск по законам и номерам"} />
    {isAlerts
      ? <AlertList items={props.alerts} selected={props.selectedAlert} onSelect={props.setSelectedAlert} />
      : <NpaList items={props.visible} selected={props.selectedNpa} onSelect={props.setSelectedNpa}
          loading={props.loading} error={props.error} />}
    <div className="sticky-add-law"><Button variant="outline" className="add-source"
      onClick={props.onAdd}><Plus />Добавить новый НПА для отслеживания</Button></div>
  </section>;
}

function NpaList({ items, selected, onSelect, loading, error }: NpaListProps) {
  return <>
    <div className="npa-list-header"><span>ДОКУМЕНТ</span><span>ИСТОЧНИК</span>
      <span>СТАДИЯ</span><span>ОБНОВЛЕНО</span></div>
    <div className="npa-list">
      {loading && <p className="empty-state"><LoaderCircle className="spin" /> Загрузка…</p>}
      {error && <p role="alert" className="form-error">{error}</p>}
      {items.map((entry) => <Button variant="ghost" key={entry.id}
        className={`npa-card ${entry.id === selected ? "selected" : ""}`}
        onClick={() => onSelect(entry.id)}><span className="npa-grid"><span>
          <strong>{entry.title}</strong><small>Законопроект № {entry.billNumber ?? "—"}</small></span>
          <span className="npa-source"><ShieldCheck size={19} />Госдума РФ</span>
          <span><Badge className={`status ${entry.trackingStatus === "published" ? "normal" : "warning"}`}>
            {entry.stage ?? "Не поддерживается"}</Badge></span>
          <span>{formatDate(entry.sourceUpdatedAt)}</span></span>
          {entry.summary && <span className="npa-alert">● Есть изменения</span>}</Button>)}
      {!loading && !error && !items.length && <p className="empty-state">Документы не найдены.</p>}
    </div>
  </>;
}

function NpaDetails({ item }: { item?: NpaItem }) {
  const [article, setArticle] = useState<number | null>(null);
  if (!item) return <p className="empty-state">Выберите документ из реестра</p>;
  const isPublished = item.trackingStatus === "published";
  return <><div className="detail-meta"><Badge className="status normal">
    {isPublished ? "• Опубликован — отслеживание завершено" : "• Отслеживается"}</Badge>
    <span>Проверка: {formatDateTime(item.lastCheckedAt)}</span></div>
    <h2>{item.title}</h2><p className="small muted">Законопроект № {item.billNumber} · Госдума РФ</p>
    <a className="npa-source-link" href={item.url} target="_blank" rel="noreferrer">
      Открыть на сайте Госдумы <ExternalLink size={14} /></a>
    <section className="article-changes"><h3>Изменённые статьи</h3>
      {item.articleChanges.length ? <ul>{item.articleChanges.map((change, index) => <li key={`${change.article}-${index}`}>
        <Button variant="ghost" onClick={() => setArticle(article === index ? null : index)}>
          {change.article}. {change.summary} {article === index ? <X size={14} /> : <Plus size={14} />}</Button>
        {article === index && <p className="article-explanation"><Sparkles size={14} />
          {change.before} → {change.after}</p>}</li>)}</ul>
        : <p className="muted small">Для текущей версии изменений текста ещё нет.</p>}</section>
    <div className="summary-box"><h3><Sparkles />Общее саммари изменений</h3>
      <p>{item.summary ?? "Это первая сохранённая версия законопроекта."}</p></div>
  </>;
}

function AlertList({ items, selected, onSelect }: AlertListProps) {
  return <div className="npa-list">{items.map((entry) => <Button variant="ghost" key={entry.id}
    className={`news-card ${entry.priority} ${entry.id === selected ? "selected" : ""}`}
    onClick={() => onSelect(entry.id)}><span className="card-meta"><span>{entry.source} · {entry.time}</span>
      <span>Сигнал о НПА</span></span><strong>{entry.title}</strong>
      <span className="excerpt">{entry.excerpt}</span></Button>)}</div>;
}

function AlertDetails({ item, onAdd }: { item?: NewsItem; onAdd: () => void }) {
  if (!item) return <p className="empty-state">Выберите новость</p>;
  return <><div className="detail-meta"><Badge className={`status ${item.priority}`}>
    • Сигнал о НПА</Badge><span>{item.time}</span></div><h2>{item.title}</h2>
    <p className="small muted">{item.source} · новость</p><div className="summary-box">
      <h3><Sparkles />AI-САММАРИ</h3><p>{item.summary}</p></div>
    <Button className="manual-law-button" onClick={onAdd}><Plus />Добавить закон вручную</Button></>;
}

function LawDialog({ open, onOpenChange, onAdd }: LawDialogProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function handleAdd() {
    if (!isDumaBillUrl(url)) return setError("Нужна ссылка вида https://sozd.duma.gov.ru/bill/123-8");
    setSaving(true); setError("");
    try { await onAdd(url.trim()); onOpenChange(false); setUrl(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Не удалось добавить НПА"); }
    finally { setSaving(false); }
  }
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent>
    <DialogTitle>Добавить НПА для отслеживания</DialogTitle>
    <DialogDescription>Укажите карточку законопроекта на sozd.duma.gov.ru. Сервис сразу
      проверит ссылку, этап и Word-версию текста.</DialogDescription>
    <label className="form-field">Ссылка на законопроект<Input aria-label="Ссылка на закон"
      value={url} onChange={(event) => setUrl(event.target.value)}
      placeholder="https://sozd.duma.gov.ru/bill/1286425-8" /></label>
    {error && <p role="alert" className="form-error">{error}</p>}
    <DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
      <Button disabled={!url.trim() || saving} onClick={handleAdd}>
        {saving ? <LoaderCircle className="spin" /> : <Scale />}Добавить в реестр</Button></DialogFooter>
  </DialogContent></Dialog>;
}

function useNpaRegistry() {
  const [acts, setActs] = useState<NpaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let isActive = true;
    listNpa().then((loaded) => { if (isActive) { setActs(loaded); setError(""); } })
      .catch((cause) => { if (isActive) setError(cause instanceof NpaApiError
        ? cause.message : "Сервис НПА недоступен"); })
      .finally(() => { if (isActive) setLoading(false); });
    return () => { isActive = false; };
  }, []);
  const add = async (url: string) => {
    const created = await createNpa(url);
    setActs((current) => [created, ...current]);
    return created;
  };
  return { acts, loading, error, add };
}

function useVisibleNpa(acts: NpaItem[], query: string, filter: NpaFilter) {
  return useMemo(() => acts.filter((entry) => `${entry.title} ${entry.billNumber ?? ""}`
    .toLowerCase().includes(query.toLowerCase()))
    .filter((entry) => filter !== "Обновления НПА" || Boolean(entry.summary)), [acts, query, filter]);
}

function useAlerts(query: string) {
  return useMemo(() => news.filter((entry) => entry.kind === "НПА")
    .filter((entry) => `${entry.title} ${entry.source}`.toLowerCase().includes(query.toLowerCase()))
    .sort((left, right) => right.relevance - left.relevance), [query]);
}

function isDumaBillUrl(value: string) {
  try { const url = new URL(value.trim()); return url.protocol === "https:" &&
    url.hostname === "sozd.duma.gov.ru" && /^\/bill\/\d+-\d+\/?$/.test(url.pathname) &&
    !url.search && !url.hash; } catch { return false; }
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat("ru-RU").format(new Date(value)) : "—";
}

function formatDateTime(value: string | null) {
  return value ? new Intl.DateTimeFormat("ru-RU", { dateStyle: "short", timeStyle: "short" })
    .format(new Date(value)) : "ещё не выполнялась";
}

interface RegistryProps {
  filter: NpaFilter; setFilter: (value: NpaFilter) => void; query: string;
  setQuery: (value: string) => void; visible: NpaItem[]; alerts: NewsItem[];
  selectedNpa?: string; selectedAlert?: string; setSelectedNpa: (id: string) => void;
  setSelectedAlert: (id: string) => void; loading: boolean; error: string; onAdd: () => void;
}
interface NpaListProps { items: NpaItem[]; selected?: string; onSelect: (id: string) => void;
  loading: boolean; error: string; }
interface AlertListProps { items: NewsItem[]; selected?: string; onSelect: (id: string) => void; }
interface LawDialogProps { open: boolean; onOpenChange: (open: boolean) => void;
  onAdd: (url: string) => Promise<void>; }
