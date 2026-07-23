import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { ScanResultView } from "@/components/scan-result-view";
import { demoScanResult, loadScanResult } from "@/lib/scan-results";
import type { ScanResultReport } from "@/lib/scan-results";
import { requireAuth } from "@/lib/auth";

export const Route = createFileRoute("/results")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Scan Results · AI Shield" },
      { name: "description", content: "Security assessment results and findings for your AI application." },
      { property: "og:title", content: "Scan Results · AI Shield" },
      { property: "og:description", content: "Security assessment results and findings for your AI application." },
    ],
  }),
  component: ResultsPage,
});

function ResultsPage() {
  const [report] = useState<ScanResultReport>(() => loadScanResult() ?? demoScanResult());

  return (
    <AppShell>
      <ScanResultView report={report} />
    </AppShell>
  );
}
