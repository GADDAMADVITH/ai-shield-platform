import { apiRequest } from "@/lib/api/client";
import type {
  BackendConnection,
  ConnectionListResponse,
  ConnectionMethodApi,
  ConnectionTestResponse,
} from "@/lib/api/types";

export type CreateConnectionBody = {
  name: string;
  connection_method: ConnectionMethodApi;
  base_url?: string | null;
  health_endpoint?: string | null;
  api_key?: string | null;
  headers?: Record<string, unknown>;
  timeout_seconds?: number;
  verify_ssl?: boolean;
  playwright_entry_url?: string | null;
  notes?: string | null;
};

export type UpdateConnectionBody = Partial<CreateConnectionBody> & {
  status?: "unverified" | "healthy" | "unhealthy" | "error";
};

export async function listConnections(
  projectId: string,
  page = 1,
  pageSize = 50,
): Promise<ConnectionListResponse> {
  return apiRequest<ConnectionListResponse>(
    `/projects/${projectId}/connections?page=${page}&page_size=${pageSize}`,
  );
}

export async function createConnection(
  projectId: string,
  body: CreateConnectionBody,
): Promise<BackendConnection> {
  return apiRequest<BackendConnection>(`/projects/${projectId}/connections`, {
    method: "POST",
    body,
  });
}

export async function updateConnection(
  projectId: string,
  connectionId: string,
  body: UpdateConnectionBody,
): Promise<BackendConnection> {
  return apiRequest<BackendConnection>(`/projects/${projectId}/connections/${connectionId}`, {
    method: "PATCH",
    body,
  });
}

export async function deleteConnection(projectId: string, connectionId: string): Promise<void> {
  await apiRequest(`/projects/${projectId}/connections/${connectionId}`, { method: "DELETE" });
}

export async function testConnection(
  projectId: string,
  connectionId: string,
): Promise<ConnectionTestResponse> {
  return apiRequest<ConnectionTestResponse>(
    `/projects/${projectId}/connections/${connectionId}/test`,
    { method: "POST" },
  );
}
