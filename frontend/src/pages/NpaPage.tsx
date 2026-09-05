import { useState } from "react";
import { Plus, Scale, ShieldCheck, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import { news } from "@/data/news";
import { npa } from "@/data/npa";
import { SearchField } from "@/components/monitoring/Shared";
import type { NewsItem, NpaItem } from "@/types/monitoring";

type NpaFilter = "Реестр отслеживаемых НПА" | "Алерты" | "Обновления НПА";

export function NpaPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<NpaFilter>("Реестр отслеживаемых НПА");
  const [selectedNpa, setSelectedNpa] = useState(npa[0].id);
  const [selectedAlert, setSelectedAlert] = useState(news[0].id);
  const [addOpen, setAddOpen] = useState(false);
  const [lawUrl, setLawUrl] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [notice, setNotice] = useState("");

  const registry = npa.filter((entry) =>
    `${entry.title} ${entry.source} ${entry.document}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const visible = filter === "Обновления НПА" ? registry.filter((entry) => entry.updated) : registry;
  const alerts = news
    .filter((entry) => entry.kind === "НПА")
    .filter((entry) => `${entry.title} ${entry.source}`.toLowerCase().includes(query.toLowerCase()))
    .sort((left, right) => right.relevance - left.relevance);
  const npaItem = visible.find((entry) => entry.id === selectedNpa) ?? visible[0];
  const alertItem = alerts.find((entry) => entry.id === selectedAlert) ?? alerts[0];

  function addLaw() {
    if (pdfFile) {
      setAddOpen(false);
      setNotice(`Документ «${pdfFile.name}» выбран для добавления в демо.`);
      return;
    }
    try {
      const parsed = new URL(lawUrl.trim());
      if (!["http:", "https:"].includes(parsed.protocol)) throw new Error();
      setAddOpen(false);
      setNotice("Ссылка принята в демо. В рабочей версии здесь запустится разбор закона.");
    } catch {
      setNotice("Укажите полную ссылку на закон в формате https://…");
    }
  }

  return (
    <div className="content-columns npa-workspace">
      <section className="panel feed npa-registry">
        <h2>НПА</h2>
        <div className="filters">
          {(["Реестр отслеживаемых НПА", "Алерты", "Обновления НПА"] as NpaFilter[]).map((label) => (
            <Button
              key={label}
              variant="outline"
              size="sm"
              aria-pressed={filter === label}
              className={filter === label ? "active-filter" : ""}
              onClick={() => setFilter(label)}
            >
              {label}
            </Button>
          ))}
        </div>
        <SearchField
          value={query}
          onChange={setQuery}
          placeholder={filter === "Алерты" ? "Поиск по новостям и регуляторам" : "Поиск по документам, регуляторам, темам"}
        />

        {filter === "Алерты" ? (
          <div className="npa-list">
            {alerts.map((entry) => (
              <AlertCard key={entry.id} item={entry} selected={entry.id === alertItem?.id} onSelect={() => setSelectedAlert(entry.id)} />
            ))}
            {!alerts.length && <p className="empty-state">Подходящих новостей не найдено.</p>}
          </div>
        ) : (
          <>
            <div className="npa-list-header">
              <span>ДОКУМЕНТ</span><span>ИСТОЧНИК</span><span>СТАДИЯ</span><span>КОНТРОЛЬНАЯ ДАТА</span>
            </div>
            <div className="npa-list">
              {visible.map((entry) => (
                <Button variant="ghost" key={entry.id} className={`npa-card ${entry.id === npaItem?.id ? "selected" : ""}`} onClick={() => setSelectedNpa(entry.id)}>
                  <span className="npa-grid"><span><strong>{entry.title}</strong><small>{entry.document}</small></span><span className="npa-source"><ShieldCheck size={19} />{entry.source}</span><span><Badge className={`status ${entry.priority}`}>{entry.stage}</Badge></span><span>{entry.deadline.split("-").reverse().join(".")}</span></span>
                  {entry.updated && <span className="npa-alert">● Есть изменения</span>}
                </Button>
              ))}
              {!visible.length && <p className="empty-state">Документы не найдены.</p>}
            </div>
          </>
        )}
        <div className="sticky-add-law"><Button variant="outline" className="add-source" onClick={() => { setLawUrl(""); setPdfFile(null); setNotice(""); setAddOpen(true); }}><Plus />Добавить новый НПА для отслеживания</Button></div>
        <p role="status" className="notice">{notice}</p>
      </section>
      <section className="panel details" aria-label={filter === "Алерты" ? "Подробности новости" : "Подробности НПА"}>
        {filter === "Алерты" ? <AlertDetails item={alertItem} onAdd={() => { setLawUrl(""); setPdfFile(null); setNotice(""); setAddOpen(true); }} /> : <NpaDetails item={npaItem} />}
      </section>
      <LawDialog open={addOpen} onOpenChange={setAddOpen} lawUrl={lawUrl} setLawUrl={setLawUrl} pdfFile={pdfFile} setPdfFile={setPdfFile} onAdd={addLaw} />
    </div>
  );
}

function NpaDetails({ item }: { item?: NpaItem }) {
  const [article, setArticle] = useState<number | null>(null);
  if (!item) return <p className="empty-state">Выберите документ из реестра</p>;
  return <><div className="detail-meta"><Badge className="status normal">{item.updated ? "• Обновлён" : "• Без изменений"}</Badge><span>Проверка: 05.09.2026</span></div><h2>{item.title}</h2><p className="small muted">{item.document} · демонстрационный материал</p><section className="article-changes"><h3>Изменения</h3>{item.changes.length ? <ul>{item.changes.map((change, index) => <li key={change.before}><Button variant="ghost" onClick={() => setArticle(article === index ? null : index)}>{`Статья ${index + 1}. ${change.after}`} {article === index ? <X size={14} /> : <Plus size={14} />}</Button>{article === index && <p className="article-explanation"><Sparkles size={14} />LLM: {change.before} → {change.after}</p>}</li>)}</ul> : <p className="muted small">Изменений нет.</p>}</section><div className="summary-box"><h3><Sparkles />Общий вывод LLM</h3><p>{item.summary}</p></div><div className="impact-box"><h3>Влияние на GS Labs</h3><p>{item.impact}</p></div></>;
}

function AlertCard({ item, selected, onSelect }: { item: NewsItem; selected: boolean; onSelect: () => void }) {
  return <Button variant="ghost" className={`news-card ${item.priority} ${selected ? "selected" : ""}`} onClick={onSelect}><span className="card-meta"><span>{item.source} · {item.time}</span><span>Сигнал о НПА</span></span><strong>{item.title}</strong><span className="excerpt">{item.excerpt}</span></Button>;
}

function AlertDetails({ item, onAdd }: { item?: NewsItem; onAdd: () => void }) {
  if (!item) return <p className="empty-state">Выберите новость</p>;
  return <><div className="detail-meta"><Badge className={`status ${item.priority}`}>• Сигнал о НПА</Badge><span>{item.time}</span></div><h2>{item.title}</h2><p className="small muted">{item.source} · новость</p><div className="summary-box"><h3><Sparkles />AI-САММАРИ</h3><p>{item.summary}</p></div><dl className="facts"><div><dt>Кто</dt><dd>{item.who}</dd></div><div><dt>Что</dt><dd>{item.what}</dd></div><div><dt>Когда</dt><dd>{item.when}</dd></div></dl><div className="impact-box"><h3>Почему это важно для GS Labs</h3><p>{item.impact}</p></div><Button className="manual-law-button" onClick={onAdd}><Plus />Добавить закон вручную</Button></>;
}

function LawDialog({ open, onOpenChange, lawUrl, setLawUrl, pdfFile, setPdfFile, onAdd }: { open: boolean; onOpenChange: (open: boolean) => void; lawUrl: string; setLawUrl: (url: string) => void; pdfFile: File | null; setPdfFile: (file: File | null) => void; onAdd: () => void }) {
  const hasLink = Boolean(lawUrl.trim());
  const hasPdf = Boolean(pdfFile);
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogTitle>Добавить НПА для отслеживания</DialogTitle><div className="law-import-options"><label className="form-field">Вставьте ссылку на опубликованный закон<Input aria-label="Ссылка на закон" value={lawUrl} disabled={hasPdf} onChange={(event) => setLawUrl(event.target.value)} placeholder="https://…"/></label><div className="law-import-divider"><span>или</span></div><label className={`pdf-upload ${hasLink ? "is-disabled" : ""}`}><span>Или загрузите документ в формате .pdf</span><Input aria-label="Загрузить PDF" type="file" accept="application/pdf,.pdf" disabled={hasLink} onChange={(event) => setPdfFile(event.target.files?.[0] ?? null)}/>{pdfFile && <strong>{pdfFile.name}</strong>}</label></div><DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button><Button disabled={!hasLink && !hasPdf} onClick={onAdd}><Scale />Добавить в реестр</Button></DialogFooter></DialogContent></Dialog>;
}
