import { apiRequest } from "@/lib/api/client";
import type { BackendReport, ReportListResponse } from "@/lib/api/types";

export async function listReports(page = 1, pageSize = 50, projectId?: string): Promise<ReportListResponse> {
  const search = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (projectId) search.set("project_id", projectId);
  return apiRequest<ReportListResponse>(`/reports?${search.toString()}`);
}

export async function getReport(reportId: string): Promise<BackendReport> {
  return apiRequest<BackendReport>(`/reports/${reportId}`);
}

export async function getReportJson(reportId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/reports/${reportId}/json`);
}
