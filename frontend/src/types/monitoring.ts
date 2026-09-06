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
  url: string;
  billNumber: string | null;
  title: string;
  stage: string | null;
  stageCode: string | null;
  documentUrl: string | null;
  trackingStatus: "tracking" | "published" | "unsupported";
  sourceUpdatedAt: string | null;
  lastCheckedAt: string | null;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
  summary: string | null;
  articleChanges: ArticleChange[];
  versions: NpaVersion[];
}
export interface ArticleChange {
  article: string;
  summary: string;
  before: string;
  after: string;
}
export interface NpaVersion {
  id: string;
  stage: string;
  stageCode: string;
  documentUrl: string;
  sourceUpdatedAt: string;
  summary: string | null;
  articleChanges: ArticleChange[];
  createdAt: string;
}
