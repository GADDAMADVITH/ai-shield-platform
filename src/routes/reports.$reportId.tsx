import { useEffect, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { Card, Chip, SectionHeader } from "@/components/ui-primitives";
import { getReport, getReportJson } from "@/lib/api/reports";
import type { BackendReport } from "@/lib/api/types";
import { requireAuth } from "@/lib/auth";
import { FileJson } from "lucide-react";

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

type ReportDocument = {
  executive_summary?: Record<string, unknown>;
  findings?: {
    total?: number;
    items?: Array<Record<string, unknown>>;
  };
  recommendations?: Array<Record<string, unknown>>;
  assessments?: Array<Record<string, unknown>>;
  scan_summary?: Record<string, unknown>;
  project?: Record<string, unknown>;
  scan?: Record<string, unknown>;
};

function ReportDetailPage() {
  const { reportId } = Route.useParams();
  const navigate = useNavigate();
  const [meta, setMeta] = useState<BackendReport | null>(null);
  const [doc, setDoc] = useState<ReportDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [report, json] = await Promise.all([getReport(reportId), getReportJson(reportId)]);
        if (cancelled) return;
        setMeta(report);
        setDoc(json as ReportDocument);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Report not found");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  async function downloadJson() {
    try {
      const json = doc ?? (await getReportJson(reportId));
      const blob = new Blob([JSON.stringify(json, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-shield-report-${reportId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("JSON report downloaded");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Download failed");
    }
  }

  if (loading) {
    return (
      <AppShell>
        <Card className="px-6 py-16 text-center text-sm text-muted-foreground">Loading report…</Card>
      </AppShell>
    );
  }

  if (error || !meta || !doc) {
    return (
      <AppShell>
        <Card className="px-6 py-16 text-center">
          <h1 className="text-lg font-semibold tracking-tight">Report not found</h1>
          <p className="mt-2 text-sm text-muted-foreground">{error ?? "Unavailable"}</p>
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

  const executive = doc.executive_summary ?? {};
  const findings = doc.findings?.items ?? [];
  const recommendations = doc.recommendations ?? [];

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Library · Report
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">{meta.title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{meta.summary}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void downloadJson()}
            className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm"
          >
            <FileJson className="h-4 w-4" />
            Download JSON
          </button>
          <button
            type="button"
            onClick={() => void navigate({ to: "/reports" })}
            className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-sm"
          >
            Back
          </button>
        </div>
      </div>

      <section className="grid gap-3 md:grid-cols-4">
        {[
          ["Security score", executive.overall_security_score],
          ["Risk score", executive.overall_risk_score],
          ["Findings", executive.total_findings],
          ["Posture", executive.overall_security_posture],
        ].map(([label, value]) => (
          <Card key={String(label)} className="!p-4">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              {label}
            </div>
            <div className="mt-2 font-mono text-2xl tabular-nums">
              {typeof value === "number" ? Math.round(value) : String(value ?? "—")}
            </div>
          </Card>
        ))}
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <SectionHeader eyebrow="Findings" title={`${findings.length} issue(s)`} />
          <ul className="space-y-3">
            {findings.length === 0 ? (
              <li className="text-sm text-muted-foreground">No findings recorded.</li>
            ) : null}
            {findings.map((f) => (
              <li key={String(f.id)} className="rounded-xl border border-border/70 p-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{String(f.title)}</span>
                  <Chip
                    tone={
                      f.severity === "critical" || f.severity === "high"
                        ? "danger"
                        : f.severity === "medium"
                          ? "warning"
                          : "info"
                    }
                  >
                    {String(f.severity)}
                  </Chip>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{String(f.description ?? "")}</p>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <SectionHeader eyebrow="Remediation" title="Recommendations" />
          <ul className="space-y-3">
            {recommendations.length === 0 ? (
              <li className="text-sm text-muted-foreground">No recommendations.</li>
            ) : null}
            {recommendations.map((r, idx) => (
              <li key={`${String(r.title)}-${idx}`} className="rounded-xl border border-border/70 p-3">
                <div className="font-medium">{String(r.title ?? "Recommendation")}</div>
                <p className="mt-1 text-sm text-muted-foreground">{String(r.description ?? "")}</p>
              </li>
            ))}
          </ul>
        </Card>
      </section>
    </AppShell>
  );
}
