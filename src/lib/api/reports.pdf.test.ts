import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  downloadReportPdf,
  fetchReportPdf,
  triggerBrowserDownload,
} from "@/lib/api/reports";
import { exportReportPdf, resolveScanIdForExport } from "@/lib/report-export";
import type { ScanResultReport } from "@/lib/scan-results";

function sampleReport(overrides: Partial<ScanResultReport> = {}): ScanResultReport {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    scanId: "11111111-1111-4111-8111-111111111111",
    projectName: "Demo",
    env: "development",
    applicationType: "api",
    connectionMethod: "rest_api",
    profile: "Standard",
    score: 82,
    grade: "B+",
    riskLevel: "Moderate",
    scanTime: "now",
    completedAt: new Date().toISOString(),
    elapsedLabel: "01:20",
    summary: { critical: 0, high: 1, medium: 1, low: 0, passed: 10, totalTests: 12 },
    findings: [],
    breakdown: [],
    recommendations: [],
    ...overrides,
  };
}

describe("resolveScanIdForExport", () => {
  it("returns UUID scan ids", () => {
    expect(resolveScanIdForExport(sampleReport())).toBe(
      "11111111-1111-4111-8111-111111111111",
    );
  });

  it("rejects non-uuid local demo ids", () => {
    expect(
      resolveScanIdForExport(sampleReport({ id: "local-demo", scanId: undefined })),
    ).toBeNull();
  });
});

describe("PDF download flow", () => {
  const originalFetch = globalThis.fetch;
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });

  it("fetchReportPdf returns blob and filename from Content-Disposition", async () => {
    const pdfBytes = new Uint8Array([0x25, 0x50, 0x44, 0x46]); // %PDF
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(pdfBytes, {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": 'attachment; filename="ai-shield-report-demo.pdf"',
        },
      }),
    );

    const result = await fetchReportPdf("11111111-1111-4111-8111-111111111111");
    expect(result.filename).toBe("ai-shield-report-demo.pdf");
    expect(result.blob.size).toBe(4);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/reports/11111111-1111-4111-8111-111111111111/pdf"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("downloadReportPdf triggers browser download before resolving", async () => {
    const pdfBytes = new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d]);
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(pdfBytes, {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": 'attachment; filename="report.pdf"',
        },
      }),
    );

    const click = vi.fn();
    URL.createObjectURL = vi.fn().mockReturnValue("blob:mock");
    URL.revokeObjectURL = vi.fn();

    const realCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = realCreate(tag);
      if (tag === "a") {
        el.click = click;
      }
      return el;
    });

    await downloadReportPdf("11111111-1111-4111-8111-111111111111");
    expect(click).toHaveBeenCalledTimes(1);
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });

  it("exportReportPdf surfaces API failures", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "not_found", message: "Scan not found" } }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(exportReportPdf(sampleReport())).rejects.toThrow(/Scan not found|not found/i);
  });

  it("triggerBrowserDownload sets download attribute", () => {
    const click = vi.fn();
    const realCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = realCreate(tag);
      if (tag === "a") el.click = click;
      return el;
    });
    URL.createObjectURL = vi.fn().mockReturnValue("blob:x");
    URL.revokeObjectURL = vi.fn();

    triggerBrowserDownload(new Blob(["%PDF"]), "out.pdf");
    expect(click).toHaveBeenCalled();
  });
});
