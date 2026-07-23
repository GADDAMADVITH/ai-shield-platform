import { redirect } from "@tanstack/react-router";

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

export const MOCK_USER: AuthUser = {
  id: "user_001",
  name: "Advith",
  email: "advith@aishield.co",
  role: "Administrator",
};

function readFlag(storage: Storage): boolean {
  try {
    return storage.getItem(AUTH_FLAG_KEY) === "1";
  } catch {
    return false;
  }
}

function readUser(storage: Storage): AuthUser | null {
  try {
    const raw = storage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AuthUser>;
    if (!parsed || typeof parsed.name !== "string" || typeof parsed.email !== "string") return null;
    return {
      id: typeof parsed.id === "string" ? parsed.id : MOCK_USER.id,
      name: parsed.name,
      email: parsed.email,
      role: typeof parsed.role === "string" ? parsed.role : MOCK_USER.role,
    };
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return readFlag(sessionStorage) || readFlag(localStorage);
  } catch {
    return false;
  }
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    if (readFlag(sessionStorage)) {
      return readUser(sessionStorage) ?? (readFlag(localStorage) ? readUser(localStorage) : null) ?? MOCK_USER;
    }
    if (readFlag(localStorage)) {
      return readUser(localStorage) ?? MOCK_USER;
    }
    return null;
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

/** Persist a mock authenticated user session. */
export function login(remember = true, overrides: Partial<AuthUser> = {}): AuthUser {
  const user: AuthUser = {
    ...MOCK_USER,
    ...overrides,
    id: overrides.id ?? MOCK_USER.id,
    name: overrides.name ?? MOCK_USER.name,
    email: overrides.email ?? MOCK_USER.email,
    role: overrides.role ?? MOCK_USER.role,
  };
  if (typeof window === "undefined") return user;
  try {
    persistUser(user, remember);
  } catch {
    /* ignore */
  }
  return user;
}

export function logout() {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(AUTH_FLAG_KEY);
    sessionStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(AUTH_FLAG_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  } catch {
    /* ignore */
  }
}

/** Update the mock authenticated user while keeping the session flag. */
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
    const payload = JSON.stringify(next);
    const remember = localStorage.getItem(AUTH_FLAG_KEY) === "1";
    sessionStorage.setItem(AUTH_FLAG_KEY, "1");
    sessionStorage.setItem(AUTH_USER_KEY, payload);
    if (remember) {
      localStorage.setItem(AUTH_FLAG_KEY, "1");
      localStorage.setItem(AUTH_USER_KEY, payload);
    }
  } catch {
    /* ignore */
  }
  return next;
}

/** Client-side route guard for protected pages. Skips during SSR (no storage). */
export function requireAuth() {
  if (typeof window === "undefined") return;
  if (!isAuthenticated() || !getStoredUser()) {
    throw redirect({ to: "/login" });
  }
}

/** Send authenticated users away from the login page. */
export function requireGuest() {
  if (typeof window === "undefined") return;
  if (isAuthenticated()) {
    throw redirect({ to: "/" });
  }
}
