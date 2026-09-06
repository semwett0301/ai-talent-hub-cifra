import type { ArticleChange, NpaItem } from "@/types/monitoring";

interface NpaResponse {
  id: string;
  url: string;
  bill_number: string | null;
  title: string;
  stage: string | null;
  tracking_status: NpaItem["trackingStatus"];
  source_updated_at: string | null;
  last_checked_at: string | null;
  published_at: string | null;
  summary: string | null;
  article_changes: ArticleChange[];
}

export class NpaApiError extends Error {}

export async function listNpa(): Promise<NpaItem[]> {
  const response = await fetch(`${__NPA_API_PREFIX__}/`);
  return mapList(await parseResponse(response));
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
  const detail = getDetail(payload);
  throw new NpaApiError(detail ?? `Сервис НПА ответил с кодом ${response.status}`);
}

function getDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) return null;
  return typeof payload.detail === "string" ? payload.detail : null;
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
    trackingStatus: entry.tracking_status,
    sourceUpdatedAt: entry.source_updated_at,
    lastCheckedAt: entry.last_checked_at,
    publishedAt: entry.published_at,
    summary: entry.summary,
    articleChanges: entry.article_changes,
  };
}
