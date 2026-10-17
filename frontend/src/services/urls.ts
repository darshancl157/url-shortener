import { apiFetch, readError } from "./http";

export interface ShortenResult {
  short_id: string;
  short_url: string;
  long_url: string;
  expires_at: string | null;
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
