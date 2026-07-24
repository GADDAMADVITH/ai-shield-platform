import { apiRequest } from "@/lib/api/client";
import type {
  DashboardOverview,
  DashboardRecentScan,
  DashboardStatistics,
  FindingsExplorerResponse,
  ScanHistoryResponse,
} from "@/lib/api/types";

export async function getDashboardOverview(): Promise<DashboardOverview> {
  return apiRequest<DashboardOverview>("/dashboard/overview");
}

export async function getDashboardRecent(limit = 10): Promise<{
  items: DashboardRecentScan[];
  notifications: Array<Record<string, unknown>>;
}> {
  return apiRequest(`/dashboard/recent?limit=${limit}`);
}

export async function getDashboardStatistics(): Promise<DashboardStatistics> {
  return apiRequest<DashboardStatistics>("/dashboard/statistics");
}

export async function getScanHistory(params?: {
  page?: number;
  pageSize?: number;
  status?: string;
  projectId?: string;
  sort?: "newest" | "oldest" | "score_desc" | "score_asc";
}): Promise<ScanHistoryResponse> {
  const search = new URLSearchParams();
  search.set("page", String(params?.page ?? 1));
  search.set("page_size", String(params?.pageSize ?? 20));
  if (params?.status) search.set("status", params.status);
  if (params?.projectId) search.set("project_id", params.projectId);
  if (params?.sort) search.set("sort", params.sort);
  return apiRequest<ScanHistoryResponse>(`/scans/history?${search.toString()}`);
}

export async function getScanSummary(scanId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/scans/${scanId}/summary`);
}

export async function exploreFindings(params?: {
  scanId?: string;
  projectId?: string;
  severity?: string;
  category?: string;
  assessmentKey?: string;
  q?: string;
}): Promise<FindingsExplorerResponse> {
  const search = new URLSearchParams();
  if (params?.scanId) search.set("scan_id", params.scanId);
  if (params?.projectId) search.set("project_id", params.projectId);
  if (params?.severity) search.set("severity", params.severity);
  if (params?.category) search.set("category", params.category);
  if (params?.assessmentKey) search.set("assessment_key", params.assessmentKey);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return apiRequest<FindingsExplorerResponse>(`/findings${qs ? `?${qs}` : ""}`);
}
