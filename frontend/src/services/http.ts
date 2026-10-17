// Auth-aware fetch. The access token lives only in this module's memory: never in
// localStorage, never in a cookie. A page reload loses it; restoreSession() gets a new
// one from the HttpOnly refresh cookie.

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;
let onSessionExpired: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setSessionExpiredHandler(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

async function requestNewAccessToken(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/refresh", { method: "POST" });
    if (!res.ok) return null;
    const body = (await res.json()) as TokenResponse;
    return body.access_token;
  } catch {
    return null;
  }
}

/**
 * Single-flight refresh. Every caller that needs a new token at the same moment shares
 * one request. Two parallel /refresh calls would send the same cookie twice, and the
 * server would treat the second as token reuse and log the user out.
 * The Web Lock extends this across browser tabs: a second tab waits, then sends the
 * cookie the first tab's refresh just replaced.
 */
export function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    const run = navigator.locks
      ? navigator.locks.request("url-shortener-refresh", requestNewAccessToken)
      : requestNewAccessToken();
    refreshInFlight = run
      .then((token) => {
        accessToken = token;
        return token;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(path, { ...init, headers });
}

/** fetch for protected endpoints: adds the token, and on 401 refreshes once and retries. */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  let res: Response;
  try {
    res = await send(path, init);
    if (res.status === 401) {
      const token = await refreshAccessToken();
      if (!token) {
        onSessionExpired?.();
        return res;
      }
      res = await send(path, init);
    }
  } catch {
    throw new Error("Could not reach the server. Try again.");
  }
  return res;
}

export async function readError(res: Response): Promise<string> {
  try {
    const body: { detail?: unknown } = await res.json();
    // App errors return {"detail": "message"}; FastAPI validation errors return a list.
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // body was not JSON
  }
  return `Request failed (${res.status}).`;
}
