import { apiRequest, apiRequestOptionalAuth, persistTokens, clearTokens } from "@/lib/api/client";
import type { AuthResponse, BackendUser } from "@/lib/api/types";

export async function loginRequest(email: string, password: string): Promise<AuthResponse> {
  return apiRequestOptionalAuth<AuthResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export async function registerRequest(
  fullName: string,
  email: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequestOptionalAuth<AuthResponse>("/auth/register", {
    method: "POST",
    body: { full_name: fullName, email, password },
  });
}

export async function meRequest(): Promise<BackendUser> {
  return apiRequest<BackendUser>("/auth/me");
}

export async function logoutRequest(refreshToken?: string | null): Promise<void> {
  try {
    await apiRequestOptionalAuth("/auth/logout", {
      method: "POST",
      body: { refresh_token: refreshToken ?? null },
    });
  } finally {
    clearTokens();
  }
}

export function applyAuthSession(response: AuthResponse, remember: boolean): void {
  persistTokens(response.tokens.access_token, response.tokens.refresh_token, remember);
}
