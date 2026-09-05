import { useState } from "react";
import { Globe, Landmark, Plus, Rss, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Choice } from "@/components/monitoring/Shared";
import { initialSources } from "@/data/sources";
import { useSessionState } from "@/hooks/useSessionState";
import type { SourceItem } from "@/types/monitoring";

const frequencyOptions = ["каждые 30 мин", "каждый час", "каждые 3 часа", "каждые 8 часов", "каждые 24 часа", "каждые 3 дня", "каждую неделю", "каждый месяц", "каждый квартал"].map((value) => ({ value, label: value }));

export function SourcesPage() {
  const [sources, setSources] = useSessionState<SourceItem[]>("sources", initialSources);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [type, setType] = useState<SourceItem["type"]>("RSS");
  const [frequency, setFrequency] = useState(frequencyOptions[0].value);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function updateSource(id: string, patch: Partial<SourceItem>) {
    setSources(sources.map((source) => source.id === id ? { ...source, ...patch } : source));
  }
  function addSource() {
    let parsed: URL;
    try {
      parsed = new URL(url.trim());
      if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname.includes(".") || parsed.username || parsed.password) throw new Error();
    } catch {
      setError("Укажите полный адрес сайта, RSS или канала: https://…");
      return;
    }
    if (type === "Telegram" && !["t.me", "telegram.me"].includes(parsed.hostname)) {
      setError("Для Telegram используйте ссылку https://t.me/название_канала");
      return;
    }
    if (sources.some((source) => source.url.replace(/\/$/, "") === parsed.href.replace(/\/$/, ""))) {
      setError("Этот адрес уже добавлен.");
      return;
    }
    setSources([...sources, { id: crypto.randomUUID(), name: name.trim(), url: parsed.href, type, frequency, enabled: true, description: "Добавлен вручную · демо" }]);
    setOpen(false);
    setNotice(`Источник «${name.trim()}» добавлен. Сбор данных в демо не запускается.`);
  }
  return <section className="panel sources-panel sources-only"><div className="section-heading"><h2>Активные источники</h2><span className="small muted">{sources.filter((source) => source.enabled).length} из {sources.length} отслеживаются</span></div><p className="small muted">Включайте отслеживание и настраивайте частоту проверки для каждого источника.</p><Table className="source-table"><TableHeader><TableRow><TableHead>Источник</TableHead><TableHead>Тип</TableHead><TableHead>Частота</TableHead><TableHead>Отслеживание</TableHead></TableRow></TableHeader><TableBody>{sources.map((source) => { const Icon = source.type === "Telegram" ? Send : source.type === "RSS" ? Rss : Landmark; return <TableRow key={source.id} className={source.enabled ? "" : "source-disabled"}><TableCell><div className="source-identity"><span className="source-icon"><Icon size={25} /></span><div><strong>{source.name}</strong><p>{source.description}</p></div></div></TableCell><TableCell className="source-type">{source.type}</TableCell><TableCell><Choice label={`Частота ${source.name}`} value={source.frequency} onChange={(value) => updateSource(source.id, { frequency: value })} options={frequencyOptions}/></TableCell><TableCell><Switch aria-label={`Отслеживание ${source.name}`} checked={source.enabled} onCheckedChange={(enabled) => updateSource(source.id, { enabled })}/></TableCell></TableRow>})}</TableBody></Table><Button variant="outline" className="add-source" onClick={() => { setName(""); setUrl(""); setType("RSS"); setFrequency(frequencyOptions[0].value); setError(""); setOpen(true); }}><Plus />Добавить RSS, сайт или Telegram-канал</Button><p role="status" className="notice">{notice}</p><Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogTitle>Добавить источник</DialogTitle><DialogDescription>Источник появится в списке; в демо подключение и сбор данных не запускаются.</DialogDescription><form onSubmit={(event) => { event.preventDefault(); addSource(); }} className="source-form"><label className="form-field">Название<Input required maxLength={80} value={name} onChange={(event) => setName(event.target.value)} placeholder="Например, отраслевое издание"/></label><label className="form-field">Адрес<Input required value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/rss"/></label><div className="form-field"><span>Тип источника</span><Choice label="Тип источника" value={type} onChange={(value) => setType(value as SourceItem["type"])} options={["RSS", "Сайт", "Telegram"].map((value) => ({ value, label: value }))}/></div><div className="form-field"><span>Частота проверки</span><Choice label="Частота проверки" value={frequency} onChange={setFrequency} options={frequencyOptions}/></div>{error && <p role="alert" className="form-error">{error}</p>}<DialogFooter><Button variant="outline" type="button" onClick={() => setOpen(false)}>Отмена</Button><Button type="submit" disabled={!name.trim() || !url.trim()}><Globe />Добавить</Button></DialogFooter></form></DialogContent></Dialog></section>;
}
