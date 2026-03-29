import { clearToken, getToken } from './auth';

/** Backend origin (no trailing slash). Use in UI when explaining connection errors. */
export function getApiBase(): string {
  const raw =
    typeof window !== 'undefined'
      ? process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      : process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  return raw.replace(/\/$/, '');
}

export function apiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBase()}${p}`;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch(
  path: string,
  options: RequestInit & { json?: unknown } = {},
): Promise<Response> {
  const { json, headers: hdrs, ...rest } = options;
  const headers = new Headers(hdrs);
  if (json !== undefined) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(apiUrl(path), {
    ...rest,
    headers,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  return res;
}

export async function apiJson<T>(path: string, options: RequestInit & { json?: unknown } = {}): Promise<T> {
  const res = await apiFetch(path, options);
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      const j = JSON.parse(text) as { detail?: string };
      if (typeof j.detail === 'string') detail = j.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail || res.statusText, res.status, text);
  }
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}
