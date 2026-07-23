import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui-primitives";
import { ConfirmDialog } from "@/components/settings/shared";
import { ScanResultView } from "@/components/scan-result-view";
import { deleteReport, getReportById } from "@/lib/reports-store";
import { requireAuth } from "@/lib/auth";

export const Route = createFileRoute("/reports/$reportId")({
  beforeLoad: () => {
    requireAuth();
  },
  head: ({ params }) => ({
    meta: [
      { title: `Report ${params.reportId} · AI Shield` },
      { name: "description", content: "Detailed AI security assessment report." },
      { property: "og:title", content: `Report ${params.reportId} · AI Shield` },
      { property: "og:description", content: "Detailed AI security assessment report." },
    ],
  }),
  component: ReportDetailPage,
});

function ReportDetailPage() {
  const { reportId } = Route.useParams();
  const navigate = useNavigate();
  const [report] = useState(() => getReportById(reportId));
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (!report) {
    return (
      <AppShell>
        <Card className="px-6 py-16 text-center">
          <h1 className="text-lg font-semibold tracking-tight">Report not found</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            This report may have been deleted or is no longer available in the mock library.
          </p>
          <button
            type="button"
            onClick={() => void navigate({ to: "/reports" })}
            className="mt-6 inline-flex items-center gap-2 rounded-2xl border border-border bg-surface/50 px-4 py-2.5 text-sm hover:bg-hover"
          >
            Back to Reports
          </button>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <ScanResultView
        report={report}
        eyebrow="Library · Report"
        backTo={{ to: "/reports", label: "Back to Reports" }}
        primaryActionLabel="Run New Scan"
        onDelete={() => setConfirmOpen(true)}
      />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Delete report?"
        description={`Remove ${report.id} (${report.projectName}) from the reports library. This only updates local mock data.`}
        confirmLabel="Delete report"
        destructive
        onConfirm={() => {
          deleteReport(report.id);
          toast.success("Report deleted", { description: report.id });
          void navigate({ to: "/reports" });
        }}
      />
    </AppShell>
  );
}
