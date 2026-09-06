import type { ArticleChange, NpaItem, NpaVersion } from "@/types/monitoring";

interface NpaResponse {
  id: string;
  url: string;
  bill_number: string | null;
  title: string;
  stage: string | null;
  stage_code: string | null;
  document_url: string | null;
  tracking_status: NpaItem["trackingStatus"];
  source_updated_at: string | null;
  last_checked_at: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  summary: string | null;
  summary_kind: "initial" | "change" | null;
  initial_summary_status: "pending" | "ready" | "failed" | null;
  article_changes: ArticleChange[];
  versions?: NpaVersionResponse[];
}

interface NpaVersionResponse {
  id: string;
  stage: string;
  stage_code: string;
  document_url: string;
  source_updated_at: string;
  summary: string | null;
  summary_kind: "initial" | "change" | null;
  article_changes: ArticleChange[];
  created_at: string;
}

export class NpaApiError extends Error {}

export async function listNpa(signal?: AbortSignal): Promise<NpaItem[]> {
  const response = await fetch(`${__NPA_API_PREFIX__}/?limit=500`, { signal });
  return mapList(await parseResponse(response));
}

export async function getNpa(id: string, signal?: AbortSignal): Promise<NpaItem> {
  const response = await fetch(`${__NPA_API_PREFIX__}/${encodeURIComponent(id)}`, { signal });
  return mapNpa(await parseResponse(response) as NpaResponse);
}

export async function createNpa(url: string): Promise<NpaItem> {
  const response = await fetch(`${__NPA_API_PREFIX__}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return mapNpa(await parseResponse(response) as NpaResponse);
}

async function parseResponse(response: Response): Promise<unknown> {
  const payload = await response.json().catch(() => null);
  if (response.ok) return payload;
  const detail = typeof payload === "object" && payload !== null && "detail" in payload
    ? String(payload.detail)
    : "";
  throw new NpaApiError(detail || errorMessage(response.status));
}

function errorMessage(status: number) {
  if (status === 404) return "НПА больше не найден в реестре";
  if (status === 409) return "Этот законопроект уже добавлен в реестр";
  if (status === 422) return "Не удалось прочитать карточку или документ законопроекта";
  if (status === 502) return "Сайт Госдумы временно недоступен. Попробуйте позднее";
  if (status === 503) return "Не удалось подготовить AI-обзор законопроекта. Попробуйте позднее";
  return `Сервис НПА ответил с кодом ${status}`;
}

function mapList(payload: unknown): NpaItem[] {
  if (!Array.isArray(payload)) throw new NpaApiError("Сервис НПА вернул неверный ответ");
  return payload.map((entry) => mapNpa(entry as NpaResponse));
}

function mapNpa(entry: NpaResponse): NpaItem {
  return {
    id: entry.id,
    url: entry.url,
    billNumber: entry.bill_number,
    title: entry.title,
    stage: entry.stage,
    stageCode: entry.stage_code,
    documentUrl: entry.document_url,
    trackingStatus: entry.tracking_status,
    sourceUpdatedAt: entry.source_updated_at,
    lastCheckedAt: entry.last_checked_at,
    publishedAt: entry.published_at,
    createdAt: entry.created_at,
    updatedAt: entry.updated_at,
    summary: entry.summary,
    summaryKind: entry.summary_kind,
    initialSummaryStatus: entry.initial_summary_status,
    articleChanges: entry.article_changes ?? [],
    versions: (entry.versions ?? [])
      .map(mapVersion)
      .sort((left, right) => Date.parse(right.createdAt) - Date.parse(left.createdAt)),
  };
}

function mapVersion(entry: NpaVersionResponse): NpaVersion {
  return {
    id: entry.id,
    stage: entry.stage,
    stageCode: entry.stage_code,
    documentUrl: entry.document_url,
    sourceUpdatedAt: entry.source_updated_at,
    summary: entry.summary,
    summaryKind: entry.summary_kind,
    articleChanges: entry.article_changes ?? [],
    createdAt: entry.created_at,
  };
}
