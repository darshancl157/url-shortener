import {
  readError,
  refreshAccessToken,
  setAccessToken,
  apiFetch,
} from "./http";

export interface User {
  id: number;
  email: string;
  created_at: string;
}

async function postJson(path: string, body: unknown): Promise<Response> {
  try {
    return await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Could not reach the server. Try again.");
  }
}

export async function fetchMe(): Promise<User> {
  const res = await apiFetch("/api/auth/me");
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as User;
}

export async function register(email: string, password: string): Promise<void> {
  const res = await postJson("/api/auth/register", { email, password });
  if (!res.ok) throw new Error(await readError(res));
}

export async function login(email: string, password: string): Promise<User> {
  const res = await postJson("/api/auth/login", { email, password });
  if (!res.ok) throw new Error(await readError(res));
  const body = (await res.json()) as { access_token: string };
  setAccessToken(body.access_token);
  return fetchMe();
}

/** Silent login on page load, using the HttpOnly refresh cookie if there is one. */
export async function restoreSession(): Promise<User | null> {
  const token = await refreshAccessToken();
  return token ? fetchMe() : null;
}

export async function logout(): Promise<void> {
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } finally {
    setAccessToken(null);
  }
}
