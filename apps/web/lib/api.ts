import type { Lang } from "./i18n";

const TOKEN_KEY = "arth.token";

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}
export function setToken(t: string | null) {
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode): the profile just won't persist */
  }
}

let currentLang: Lang = "en";
export function setApiLang(l: Lang) {
  currentLang = l;
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown; form?: FormData; lang?: Lang; raw?: boolean } = {}): Promise<T> {
  const headers: Record<string, string> = { "X-Arth-Lang": opts.lang ?? currentLang };
  const tok = getToken();
  if (tok) headers["Authorization"] = `Bearer ${tok}`;
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method: opts.method ?? (body ? "POST" : "GET"), headers, body, cache: "no-store" });
  } catch {
    throw new ApiError(0, "network", "The local ARTHDARSHAN server is not reachable.");
  }
  if (opts.raw) {
    if (!res.ok) throw await toError(res);
    return res as unknown as T;
  }
  if (!res.ok) throw await toError(res);
  return (await res.json()) as T;
}

async function toError(res: Response): Promise<ApiError> {
  try {
    const j = await res.json();
    return new ApiError(res.status, j?.error?.code ?? "error", j?.error?.message ?? res.statusText);
  } catch {
    return new ApiError(res.status, "error", res.statusText || "Request failed");
  }
}

export async function startProfile(lang: Lang, simple = false, demo = false) {
  const j = await api<{ token: string; user: any }>(demo ? "/auth/demo" : "/auth/start", { method: "POST", body: { language: lang, simple_mode: simple, display_name: demo ? "Demo learner" : null } });
  setToken(j.token);
  return j.user;
}
