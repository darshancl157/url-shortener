const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export interface ShortenResult {
  short_id: string;
  short_url: string;
  long_url: string;
  expires_at: string | null;
}

export async function shortenUrl(longUrl: string): Promise<ShortenResult> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/shortenurl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ long_url: longUrl }),
    });
  } catch {
    throw new Error("Could not reach the server. Try again.");
  }

  if (!res.ok) {
    throw new Error(await errorMessage(res));
  }
  return (await res.json()) as ShortenResult;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body: { detail?: unknown } = await res.json();
    // App errors return {"detail": "message"}; FastAPI validation errors return a list.
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // body was not JSON
  }
  return `Request failed (${res.status}).`;
}
