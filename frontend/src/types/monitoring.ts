export type Priority = "critical" | "warning" | "normal";
export interface NewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
  ageHours: number;
  relevance: number;
  priority: Priority;
  kind: "НПА" | "Новости";
  tags: string[];
  excerpt: string;
  summary: string;
  who: string;
  what: string;
  when: string;
  impact: string;
  articleChanges: { title: string; explanation: string }[];
}
export interface NpaItem {
  id: string;
  title: string;
  document: string;
  source: string;
  stage: string;
  priority: Priority;
  deadline: string;
  owner: string;
  initials: string;
  alert: string;
  updated: boolean;
  summary: string;
  impact: string;
  changes: { before: string; after: string }[];
  versions: { date: string; label: string }[];
}
