// Typed API client with automatic refresh-token rotation.
//
// Token strategy: access token lives in MEMORY only (XSS can't read what isn't
// stored); the refresh token sits in localStorage as a deliberate, documented
// tradeoff for a portfolio SPA (the alternative — httpOnly cookies — needs
// CSRF machinery; noted in module-06 doc).

import type {
  Analysis,
  AnalysisAccepted,
  AnalysisListItem,
  ApiError,
  ChatHistory,
  ErrorGroup,
  Investigation,
  Page,
  Report,
  SimilarResponse,
  TimelineEvent,
  TokenResponse,
  User,
} from "./types";

const BASE = "/api/v1";
const REFRESH_KEY = "ala_refresh_token";

let accessToken: string | null = null;

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

function storeTokens(tokens: TokenResponse): void {
  accessToken = tokens.access_token;
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  accessToken = null;
  localStorage.removeItem(REFRESH_KEY);
}

export function hasSession(): boolean {
  return localStorage.getItem(REFRESH_KEY) !== null;
}

async function refresh(): Promise<boolean> {
  const token = localStorage.getItem(REFRESH_KEY);
  if (!token) return false;
  const resp = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: token }),
  });
  if (!resp.ok) {
    clearTokens();
    return false;
  }
  storeTokens((await resp.json()) as TokenResponse);
  return true;
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });

  if (resp.status === 401 && retry && (await refresh())) {
    return request<T>(path, init, false); // one retry with the fresh token
  }
  if (!resp.ok) {
    const body = (await resp.json().catch(() => null)) as ApiError | null;
    throw new ApiRequestError(
      resp.status,
      body?.error.code ?? "unknown",
      body?.error.message ?? `Request failed (${resp.status})`,
    );
  }
  return (await resp.json()) as T;
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  async register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", jsonInit("POST", { email, password }));
  },
  async login(email: string, password: string): Promise<void> {
    storeTokens(
      await request<TokenResponse>("/auth/login", jsonInit("POST", { email, password })),
    );
  },
  async restoreSession(): Promise<User | null> {
    if (!hasSession() || !(await refresh())) return null;
    return request<User>("/users/me").catch(() => null);
  },
  me: () => request<User>("/users/me"),
  pasteLog: (content: string, filename = "pasted.log") =>
    request<AnalysisAccepted>("/logs/paste", jsonInit("POST", { content, filename })),
  uploadLog: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<AnalysisAccepted>("/logs", { method: "POST", body: form });
  },
  analysis: (id: string) => request<Analysis>(`/analyses/${id}`),
  groups: (id: string, limit = 50) =>
    request<Page<ErrorGroup>>(`/analyses/${id}/groups?limit=${limit}`),
  similar: (id: string) => request<SimilarResponse>(`/analyses/${id}/similar`),
  history: (limit = 20, offset = 0) =>
    request<Page<AnalysisListItem>>(`/analyses?limit=${limit}&offset=${offset}`),
  chatHistory: (logFileId: string) => request<ChatHistory>(`/logs/${logFileId}/chat`),
  generateReport: (id: string) => request<Report>(`/analyses/${id}/report`, { method: "POST" }),
  getReport: (id: string) => request<Report>(`/analyses/${id}/report`),
  reportDownloadUrl: (id: string) => `/api/v1/analyses/${id}/report.md`,
  timeline: (id: string) => request<{ events: TimelineEvent[] }>(`/analyses/${id}/timeline`),
  investigate: (id: string) =>
    request<Investigation>(`/analyses/${id}/investigate`, { method: "POST" }),
  logout: clearTokens,
};

export interface StreamEvent {
  type: "token" | "done" | "error";
  text?: string;
  message?: string;
  citations?: { start_line: number; end_line: number }[];
}

// SSE via fetch + ReadableStream: EventSource can't send Authorization headers.
export async function chatStream(
  logFileId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const doFetch = () =>
    fetch(`${BASE}/logs/${logFileId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({ message }),
    });

  let resp = await doFetch();
  if (resp.status === 401 && (await refresh())) resp = await doFetch();
  if (!resp.ok || !resp.body) {
    onEvent({ type: "error", message: `Chat failed (${resp.status})` });
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      if (part.startsWith("data: ")) onEvent(JSON.parse(part.slice(6)) as StreamEvent);
    }
  }
}
