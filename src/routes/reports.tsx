import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { Search, ChevronRight, FileJson, Play, FileText } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card, Chip } from "@/components/ui-primitives";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import { listReports, getReportJson } from "@/lib/api/reports";
import type { BackendReport } from "@/lib/api/types";
import { requireAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reports")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Reports · AI Shield" },
      {
        name: "description",
        content: "Executive-ready AI security reports and compliance artifacts.",
      },
      { property: "og:title", content: "Reports · AI Shield" },
      {
        property: "og:description",
        content: "Executive-ready AI security reports and compliance artifacts.",
      },
    ],
  }),
  component: Reports,
});

function riskTone(score: number | null): "success" | "warning" | "danger" | "info" {
  if (score == null) return "info";
  if (score >= 85) return "success";
  if (score >= 70) return "warning";
  return "danger";
}

function Reports() {
  const { openStartScan } = useScanWorkflow();
  const [reports, setReports] = useState<BackendReport[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const page = await listReports(1, 50);
        if (!cancelled) setReports(page.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load reports");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return reports;
    return reports.filter(
      (r) =>
        r.title.toLowerCase().includes(q) ||
        (r.project_name ?? "").toLowerCase().includes(q) ||
        r.id.toLowerCase().includes(q),
    );
  }, [reports, search]);

  async function downloadJson(report: BackendReport) {
    try {
      const doc = await getReportJson(report.id);
      const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-shield-report-${report.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("JSON report downloaded");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Download failed");
    }
  }

  const hasAny = reports.length > 0;

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Library
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Completed security assessments across your AI applications.
          </p>
        </div>
        <button
          type="button"
          onClick={() => openStartScan()}
          className="inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
        >
          <Play className="h-4 w-4" />
          Run scan
        </button>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search reports…"
            className="w-full bg-transparent outline-none placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}

      {!loading && !hasAny ? (
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <FileText className="h-8 w-8 text-muted-foreground" />
          <div>
            <h2 className="text-lg font-medium">No reports yet</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Run a scan to generate an executive security report.
            </p>
          </div>
        </Card>
      ) : null}

      <div className="grid gap-3">
        {filtered.map((report) => (
          <Card
            key={report.id}
            className={cn(
              "group flex flex-wrap items-center gap-4 !p-4 transition-colors hover:bg-hover/30",
            )}
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Link
                  to="/reports/$reportId"
                  params={{ reportId: report.id }}
                  className="truncate font-medium hover:underline"
                >
                  {report.title}
                </Link>
                <Chip tone={riskTone(report.overall_security_score)}>{report.status}</Chip>
              </div>
              <div className="mt-1 flex flex-wrap gap-3 font-mono text-[11px] text-muted-foreground">
                <span>{report.project_name ?? "Project"}</span>
                <span>
                  Score{" "}
                  {report.overall_security_score != null
                    ? Math.round(report.overall_security_score)
                    : "—"}
                </span>
                <span>{report.total_findings ?? 0} findings</span>
                <span>{new Date(report.created_at).toLocaleString()}</span>
              </div>
              {report.summary ? (
                <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{report.summary}</p>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => downloadJson(report)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
              >
                <FileJson className="h-3.5 w-3.5" />
                JSON
              </button>
              <Link
                to="/reports/$reportId"
                params={{ reportId: report.id }}
                className="inline-flex items-center gap-1 rounded-xl border border-border px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
              >
                Open <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
