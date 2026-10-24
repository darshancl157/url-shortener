import { apiFetch, readError } from "./http";

export interface ShortenResult {
  short_id: string;
  short_url: string;
  long_url: string;
  expires_at: string | null;
}

export interface UrlItem {
  short_id: string;
  short_url: string;
  long_url: string;
  created_at: string;
  expires_at: string | null;
  click_count: number;
  is_disabled: boolean;
}

export interface UrlPage {
  items: UrlItem[];
  total: number;
  limit: number;
  offset: number;
}

export async function listUrls(
  limit: number,
  offset: number,
): Promise<UrlPage> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await apiFetch(`/api/urls?${query}`);
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as UrlPage;
}

export async function shortenUrl(longUrl: string): Promise<ShortenResult> {
  const res = await apiFetch("/api/shortenurl", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ long_url: longUrl }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as ShortenResult;
}
