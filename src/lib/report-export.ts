import { downloadReportPdf } from "@/lib/api/reports";
import type { ScanResultReport } from "@/lib/scan-results";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function resolveScanIdForExport(report: ScanResultReport): string | null {
  const candidate = report.scanId ?? report.id;
  return UUID_RE.test(candidate) ? candidate : null;
}

export async function exportReportPdf(report: ScanResultReport): Promise<void> {
  const scanId = resolveScanIdForExport(report);
  if (!scanId) {
    throw new Error(
      "PDF export requires a backend scan. Run a live scan, then export from the completed report.",
    );
  }
  await downloadReportPdf(scanId);
}
