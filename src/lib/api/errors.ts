import type { ApiErrorBody } from "@/lib/api/types";

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function messageForApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return error.message || "Please sign in again.";
    if (error.status === 403) return error.message || "You do not have permission to do that.";
    if (error.status === 404) return error.message || "Resource not found.";
    if (error.status === 409) return error.message || "Conflict — that resource already exists.";
    if (error.status >= 500) return "Server error. Please try again shortly.";
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export function parseApiError(status: number, body: unknown): ApiError {
  const parsed = body as ApiErrorBody | null;
  const code = parsed?.error?.code ?? "http_error";
  const message = parsed?.error?.message ?? `Request failed (${status})`;
  return new ApiError(status, code, message, parsed?.error?.details);
}
