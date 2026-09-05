import type { LucideIcon } from "lucide-react";
import { Eye, Filter, ShieldCheck, Zap, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

export function SearchField({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div className="search-field">
      <Search size={17} />
      <Input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
export function Choice({
  value,
  onChange,
  options,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  label: string;
}) {
  return (
    <Select
      value={value}
      onValueChange={(v) => {
        if (v !== null) onChange(v);
      }}
      items={options}
    >
      <SelectTrigger aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
export function FeatureStrip({
  items,
}: {
  items?: { title: string; text: string; icon: LucideIcon }[];
}) {
  const entries = items ?? [
    {
      title: "Быстрее увидеть",
      text: "Сбор по расписанию, парсеры, очередь обработки.",
      icon: Eye,
    },
    {
      title: "Не утонуть в шуме",
      text: "Актуализация, релевантность, объяснимая приоритизация.",
      icon: Filter,
    },
    {
      title: "Доверять результату",
      text: "Почему это важно, источник и проверка человеком.",
      icon: ShieldCheck,
    },
    {
      title: "Довести до действия",
      text: "Дайджест, контроль НПА, статусы и ручное редактирование.",
      icon: Zap,
    },
  ];
  return (
    <footer className="feature-strip">
      {entries.map(({ title, text, icon: Icon }) => (
        <div className="feature panel" key={title}>
          <span className="feature-icon">
            <Icon />
          </span>
          <div>
            <strong>{title}</strong>
            <p>{text}</p>
          </div>
        </div>
      ))}
    </footer>
  );
}
