import type { SourceItem } from "@/types/monitoring";
export const initialSources: SourceItem[] = [
  {
    id: "rkn",
    name: "Роскомнадзор",
    description: "Сайт регулятора",
    type: "Сайт",
    frequency: "каждые 30 мин",
    enabled: true,
    url: "https://rkn.gov.ru",
  },
  {
    id: "duma",
    name: "Госдума",
    description: "Законопроекты и документы",
    type: "Сайт",
    frequency: "каждые 30 мин",
    enabled: true,
    url: "https://duma.gov.ru",
  },
  {
    id: "kommersant",
    name: "Коммерсантъ",
    description: "Новости и аналитика",
    type: "RSS",
    frequency: "каждые 30 мин",
    enabled: true,
    url: "https://kommersant.ru",
  },
  {
    id: "digital",
    name: "Digital Russia",
    description: "Telegram-канал",
    type: "Telegram",
    frequency: "каждые 30 мин",
    enabled: true,
    url: "https://t.me/digital_russia",
  },
  {
    id: "digitalgov",
    name: "Минцифры",
    description: "Сайт / RSS",
    type: "Сайт / RSS",
    frequency: "каждые 30 мин",
    enabled: true,
    url: "https://digital.gov.ru",
  },
  {
    id: "rbc",
    name: "РБК",
    description: "Новости и аналитика",
    type: "RSS",
    frequency: "каждые 24 часа",
    enabled: false,
    url: "https://rbc.ru",
  },
];
export const monitoringRules = [
  {
    id: "archive",
    label: "Архивировать обычные новости через 72 часа",
    icon: "clock",
  },
  {
    id: "critical",
    label: "Критичные материалы оставлять в ленте",
    icon: "shield",
  },
  {
    id: "alert",
    label: "Создавать AI-alert по сигналам о НПА",
    icon: "sparkles",
  },
  {
    id: "editing",
    label: "Разрешить ручное редактирование саммари и метаданных",
    icon: "pencil",
  },
  {
    id: "batch",
    label: "Использовать микробатч AI-саммаризации",
    icon: "settings",
  },
];
export const controlRules = [
  { id: "history", label: "Хранить историю версий", icon: "database" },
  { id: "diff", label: "Строить diff: было / стало", icon: "arrows" },
  { id: "highlight", label: "Подсвечивать изменённые статьи", icon: "pencil" },
  {
    id: "summary",
    label: "Формировать саммари влияния на GS Labs",
    icon: "file",
  },
  {
    id: "notify",
    label: "Уведомлять ответственного при новой версии",
    icon: "bell",
  },
];
