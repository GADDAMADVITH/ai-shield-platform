import { ApiError, parseApiError } from "@/lib/api/errors";
import { apiRequest, getAccessToken, getApiBaseUrl, enqueueRefreshForDownload } from "@/lib/api/client";
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

export type PdfDownloadResult = {
  blob: Blob;
  filename: string;
};

/**
 * Fetch the PDF report for a scan and return a Blob ready for browser download.
 */
export async function fetchReportPdf(scanId: string, options?: { skipRefresh?: boolean }): Promise<PdfDownloadResult> {
  const headers: Record<string, string> = {
    Accept: "application/pdf",
  };
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${getApiBaseUrl()}/reports/${encodeURIComponent(scanId)}/pdf`, {
    method: "GET",
    headers,
  });

  if (response.status === 401 && !options?.skipRefresh) {
    const refreshed = await enqueueRefreshForDownload();
    if (refreshed) {
      return fetchReportPdf(scanId, { skipRefresh: true });
    }
  }

  if (!response.ok) {
    const text = await response.text();
    let body: unknown = null;
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = { error: { code: "download_failed", message: text || "PDF download failed" } };
      }
    }
    throw parseApiError(response.status, body);
  }

  const blob = await response.blob();
  if (!blob.type.includes("pdf") && blob.size === 0) {
    throw new ApiError(500, "invalid_pdf", "PDF export returned an empty file.");
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";]+)"?/i.exec(disposition);
  const filename = match?.[1] ?? `ai-shield-report-${scanId}.pdf`;
  return { blob, filename };
}

/** Trigger a browser file download for the given blob. */
export function triggerBrowserDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}

/**
 * Download the PDF for a scan. Resolves only after the download has been triggered.
 */
export async function downloadReportPdf(scanId: string): Promise<PdfDownloadResult> {
  const result = await fetchReportPdf(scanId);
  triggerBrowserDownload(result.blob, result.filename);
  return result;
}
