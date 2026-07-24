import { ApiError, parseApiError } from "@/lib/api/errors";

const ACCESS_KEY = "ais-access-token";
const REFRESH_KEY = "ais-refresh-token";
const REMEMBER_KEY = "ais-remember";

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(ACCESS_KEY) ?? localStorage.getItem(ACCESS_KEY);
  } catch {
    return null;
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(REFRESH_KEY) ?? localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export function persistTokens(
  accessToken: string,
  refreshToken: string,
  remember: boolean,
): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(ACCESS_KEY, accessToken);
  sessionStorage.setItem(REFRESH_KEY, refreshToken);
  sessionStorage.setItem(REMEMBER_KEY, remember ? "1" : "0");
  if (remember) {
    localStorage.setItem(ACCESS_KEY, accessToken);
    localStorage.setItem(REFRESH_KEY, refreshToken);
    localStorage.setItem(REMEMBER_KEY, "1");
  } else {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(REMEMBER_KEY);
  }
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  for (const key of [ACCESS_KEY, REFRESH_KEY, REMEMBER_KEY]) {
    sessionStorage.removeItem(key);
    localStorage.removeItem(key);
  }
}

export function isRememberedSession(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return (
      sessionStorage.getItem(REMEMBER_KEY) === "1" || localStorage.getItem(REMEMBER_KEY) === "1"
    );
  } catch {
    return false;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
  headers?: Record<string, string>;
  /** Skip automatic refresh retry (used by refresh itself). */
  skipRefresh?: boolean;
};

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      clearTokens();
      return false;
    }
    const data = (await response.json()) as {
      tokens: { access_token: string; refresh_token: string };
    };
    persistTokens(data.tokens.access_token, data.tokens.refresh_token, isRememberedSession());
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

function enqueueRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

/** Shared refresh helper for non-JSON downloads (PDF, etc.). */
export function enqueueRefreshForDownload(): Promise<boolean> {
  return enqueueRefresh();
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...options.headers,
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options.method ?? (options.body !== undefined ? "POST" : "GET"),
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 401 && options.auth !== false && !options.skipRefresh) {
    const refreshed = await enqueueRefresh();
    if (refreshed) {
      return apiRequest<T>(path, { ...options, skipRefresh: true });
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { error: { code: "parse_error", message: text } };
    }
  }

  if (!response.ok) {
    throw parseApiError(response.status, body);
  }

  return body as T;
}

export async function apiRequestOptionalAuth<T>(
  path: string,
  options: Omit<RequestOptions, "auth"> = {},
): Promise<T> {
  return apiRequest<T>(path, { ...options, auth: false });
}

export { ApiError };
