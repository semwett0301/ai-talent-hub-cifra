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
  summaryKind: "initial" | "change" | null;
  initialSummaryStatus: "pending" | "ready" | "failed" | null;
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
  summaryKind: "initial" | "change" | null;
  articleChanges: ArticleChange[];
  createdAt: string;
}
