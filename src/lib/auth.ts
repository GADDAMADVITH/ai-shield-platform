import { redirect } from "@tanstack/react-router";
import {
  applyAuthSession,
  loginRequest,
  logoutRequest,
  meRequest,
  registerRequest,
} from "@/lib/api/auth";
import { clearTokens, getAccessToken, getRefreshToken } from "@/lib/api/client";
import { mapBackendUser } from "@/lib/api/mappers";

export const AUTH_FLAG_KEY = "ais-auth";
export const AUTH_USER_KEY = "ais-auth-user";

/** @deprecated use AUTH_FLAG_KEY */
export const AUTH_KEY = AUTH_FLAG_KEY;

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: string;
};

function readUser(storage: Storage): AuthUser | null {
  try {
    const raw = storage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AuthUser>;
    if (!parsed || typeof parsed.name !== "string" || typeof parsed.email !== "string") return null;
    return {
      id: typeof parsed.id === "string" ? parsed.id : "",
      name: parsed.name,
      email: parsed.email,
      role: typeof parsed.role === "string" ? parsed.role : "Member",
    };
  } catch {
    return null;
  }
}

function persistUser(user: AuthUser, remember: boolean) {
  const payload = JSON.stringify(user);
  sessionStorage.setItem(AUTH_FLAG_KEY, "1");
  sessionStorage.setItem(AUTH_USER_KEY, payload);
  if (remember) {
    localStorage.setItem(AUTH_FLAG_KEY, "1");
    localStorage.setItem(AUTH_USER_KEY, payload);
  } else {
    localStorage.removeItem(AUTH_FLAG_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return Boolean(getAccessToken());
  } catch {
    return false;
  }
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    return readUser(sessionStorage) ?? readUser(localStorage);
  } catch {
    return null;
  }
}

export async function loginWithCredentials(
  email: string,
  password: string,
  remember = true,
): Promise<AuthUser> {
  const response = await loginRequest(email, password);
  applyAuthSession(response, remember);
  const user = mapBackendUser(response.user);
  persistUser(user, remember);
  return user;
}

export async function registerAccount(
  fullName: string,
  email: string,
  password: string,
  remember = true,
): Promise<AuthUser> {
  const response = await registerRequest(fullName, email, password);
  applyAuthSession(response, remember);
  const user = mapBackendUser(response.user);
  persistUser(user, remember);
  return user;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  if (!getAccessToken()) return null;
  const backendUser = await meRequest();
  const user = mapBackendUser(backendUser);
  const remember =
    localStorage.getItem(AUTH_FLAG_KEY) === "1" || localStorage.getItem("ais-remember") === "1";
  persistUser(user, remember);
  return user;
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  await logoutRequest(refresh);
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(AUTH_FLAG_KEY);
    sessionStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(AUTH_FLAG_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  } catch {
    /* ignore */
  }
  clearTokens();
}

export function updateStoredUser(partial: Partial<AuthUser>): AuthUser | null {
  if (typeof window === "undefined") return null;
  const current = getStoredUser();
  if (!current) return null;
  const next: AuthUser = {
    ...current,
    ...partial,
    id: partial.id ?? current.id,
    name: partial.name ?? current.name,
    email: partial.email ?? current.email,
    role: partial.role ?? current.role,
  };
  try {
    const remember = localStorage.getItem(AUTH_FLAG_KEY) === "1";
    persistUser(next, remember);
  } catch {
    /* ignore */
  }
  return next;
}

export function requireAuth() {
  if (typeof window === "undefined") return;
  if (!isAuthenticated()) {
    throw redirect({ to: "/login" });
  }
}

export function requireGuest() {
  if (typeof window === "undefined") return;
  if (isAuthenticated()) {
    throw redirect({ to: "/" });
  }
}
