import { useSessionState } from "@/hooks/useSessionState";
import { useState } from "react";
import {
  EyeOff,
  Pencil,
  Sparkles,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { news } from "@/data/news";
import type { NewsItem } from "@/types/monitoring";
import {
  Choice,
  SearchField,
} from "@/components/monitoring/Shared";

export function NewsPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("Все");
  const [period, setPeriod] = useState("24");
  const [selected, setSelected] = useState(news[0].id);
  const [hidden, setHidden] = useSessionState<string[]>("news-hidden", []);
  const [edits, setEdits] = useSessionState<Record<string, string>>(
    "news-edits",
    {},
  );
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [notice, setNotice] = useState("");
  const visible = news.filter(
    (item) =>
      !hidden.includes(item.id) &&
      item.ageHours <= Number(period) &&
      (filter === "Все" ||
        (filter === "Требует внимания" && item.priority === "critical") ||
        item.kind === filter) &&
      `${item.title} ${item.source} ${item.tags.join(" ")}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  ).sort((left, right) => right.relevance - left.relevance);
  const item = visible.find((item) => item.id === selected) ?? visible[0];
  return (
    <>
      <div className="content-columns">
        <section className="panel feed">
          <div className="section-heading">
            <h2>
              Входящие <span>{visible.length}</span>
            </h2>
            <span className="small muted">Сегодня, 5 сентября</span>
          </div>
          <SearchField
            value={query}
            onChange={setQuery}
            placeholder="Поиск по тексту, тегам и организациям"
          />
          <div className="filters">
            {["Все", "Требует внимания", "Новости"].map((label) => (
              <Button
                key={label}
                size="sm"
                variant="outline"
                aria-pressed={filter === label}
                className={filter === label ? "active-filter" : ""}
                onClick={() => setFilter(label)}
              >
                {label}
              </Button>
            ))}
            <Choice
              label="Период новостей"
              value={period}
              onChange={setPeriod}
              options={[
                { value: "24", label: "За 24 часа" },
                { value: "72", label: "За 3 дня" },
              ]}
            />
          </div>
          <div className="news-list">
            {visible.map((entry) => (
              <NewsCard
                key={entry.id}
                item={entry}
                selected={entry.id === item?.id}
                onSelect={() => setSelected(entry.id)}
              />
            ))}
            {!visible.length && (
              <div className="empty-state">
                Материалы не найдены. Измените запрос или фильтры.
              </div>
            )}
          </div>
          {hidden.length > 0 && (
            <Button
              variant="ghost"
              className="restore"
              onClick={() => {
                setHidden([]);
                setNotice("Скрытые материалы восстановлены");
              }}
            >
              <RotateCcw />
              Вернуть скрытые ({hidden.length})
            </Button>
          )}
        </section>
        <section className="panel details" aria-label="Подробности новости">
          {item ? (
            <>
              <div className="detail-meta">
                <Badge className={`status ${item.priority}`}>
                  {item.priority === "critical"
                    ? "• Требует внимания"
                    : item.priority === "warning"
                      ? "• Важно"
                      : "• Информация"}
                </Badge>
                <span>{item.time}</span>
              </div>
              <h2>{item.title}</h2>
              <p className="muted small">
                {item.source} · {item.kind} ·{" "}
                <span className="mock-note">демонстрационный материал</span>
              </p>
              <div className="summary-box">
                <h3>
                  <Sparkles />
                  AI-САММАРИ
                </h3>
                <p>{edits[item.id] ?? item.summary}</p>
                {edits[item.id] && <small>Отредактировано вручную</small>}
              </div>
              <div className="impact-box">
                <h3>Почему это важно для GS Labs</h3>
                <p>{item.impact}</p>
              </div>
              <div className="actions">
                <Button
                  variant="outline"
                  onClick={() => {
                    setDraft(edits[item.id] ?? item.summary);
                    setEditing(true);
                  }}
                >
                  <Pencil />
                  Редактировать
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setHidden([...hidden, item.id]);
                    setNotice("Материал скрыт. Его можно вернуть под списком.");
                  }}
                >
                  <EyeOff />
                  Скрыть
                </Button>
              </div>
            </>
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
          <DialogDescription>
            Правки сохраняются в текущей демонстрационной сессии.
          </DialogDescription>
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
            <Button
              disabled={!draft.trim()}
              onClick={() => {
                if (item) setEdits({ ...edits, [item.id]: draft.trim() });
                setEditing(false);
                setNotice("Саммари обновлено");
              }}
            >
              Сохранить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
function NewsCard({
  item,
  selected,
  onSelect,
}: {
  item: NewsItem;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <Button
      variant="ghost"
      className={`news-card ${item.priority} ${selected ? "selected" : ""}`}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className="card-meta">
        <span>
          {item.source} · {item.time}
        </span>
        <span>{getNoiseLabel(item.relevance)}</span>
      </span>
      <strong>{item.title}</strong>
      <span className="excerpt">{item.excerpt}</span>
      <span className="tags">
        {item.tags.map((tag) => (
          <Badge variant="secondary" key={tag}>
            {tag}
          </Badge>
        ))}
      </span>
    </Button>
  );
}

function getNoiseLabel(score: number) {
  if (score < 50) return "Шум";
  if (score < 65) return "Релевантно";
  if (score < 80) return "Важно";
  return "Горячая новость";
}
