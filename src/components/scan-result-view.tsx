import { useMemo } from "react";
import { Link } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  Download,
  FileJson,
  Share2,
  Play,
  ArrowLeft,
  ShieldAlert,
  CheckCircle2,
  Trash2,
} from "lucide-react";
import { Card, Chip, ScoreRing, SectionHeader, StatusDot } from "@/components/ui-primitives";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Progress } from "@/components/ui/progress";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import type { FindingSeverity, ScanResultReport } from "@/lib/scan-results";
import { pushNotification } from "@/lib/notifications-store";
import { cn } from "@/lib/utils";

function severityTone(sev: FindingSeverity): "danger" | "warning" | "info" | "success" | "muted" {
  if (sev === "critical" || sev === "high") return "danger";
  if (sev === "medium") return "warning";
  if (sev === "low") return "info";
  return "muted";
}

export function riskTone(risk: ScanResultReport["riskLevel"]): "success" | "warning" | "danger" | "info" {
  if (risk === "Low") return "success";
  if (risk === "Moderate") return "info";
  if (risk === "Elevated") return "warning";
  return "danger";
}

export function executiveSummaryText(report: ScanResultReport) {
  const open = report.findings.filter((f) => f.status === "Open").length;
  const posture =
    report.score >= 90
      ? "strong"
      : report.score >= 80
        ? "acceptable with residual risk"
        : report.score >= 70
          ? "elevated risk requiring remediation"
          : "high risk and needs immediate attention";

  return `AI Shield completed a ${report.profile.toLowerCase()} against ${report.projectName} (${report.applicationType}) in ${report.env}. Overall security score is ${report.score} (Grade ${report.grade}, ${report.riskLevel} risk) — ${posture}. ${report.summary.totalTests} controls were evaluated with ${report.summary.passed} passing. ${open} finding${open === 1 ? "" : "s"} remain open across critical (${report.summary.critical}), high (${report.summary.high}), medium (${report.summary.medium}), and low (${report.summary.low}) severities.`;
}

export function buildReportTimeline(report: ScanResultReport) {
  const end = new Date(report.completedAt);
  const parts = report.elapsedLabel.split(":").map((n) => Number(n) || 0);
  const elapsedMs = ((parts[0] ?? 0) * 60 + (parts[1] ?? 0)) * 1000;
  const start = new Date(end.getTime() - Math.max(elapsedMs, 60_000));
  const mid = new Date(start.getTime() + elapsedMs * 0.45);
  const analyze = new Date(start.getTime() + elapsedMs * 0.75);

  const fmt = (d: Date) =>
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return [
    { t: fmt(start), l: `Scan started · ${report.profile} · ${report.env}` },
    { t: fmt(mid), l: `Running assessments · ${report.summary.totalTests} controls queued` },
    {
      t: fmt(analyze),
      l: `Analyzing findings · ${report.findings.length} issue${report.findings.length === 1 ? "" : "s"} detected`,
    },
    {
      t: fmt(end),
      l: `Report finalized · score ${report.score} · ${report.riskLevel} risk`,
    },
  ];
}

export function mockExportReport(report: ScanResultReport, kind: "PDF" | "JSON" | "Share") {
  if (kind === "JSON") {
    try {
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${report.projectName}-${report.id}-report.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    }
  }
  toast.success(
    kind === "Share" ? "Share link copied (mock)." : `${kind} export ready (mock).`,
    { description: `${report.projectName} · ${report.id}` },
  );
  if (kind === "PDF" || kind === "JSON") {
    pushNotification({
      title: "Report Generated",
      description: `Security report exported successfully (${kind}) for ${report.projectName}.`,
      category: "reports",
      severity: "info",
    });
  }
}

function FindingBlock({ label, body }: { label: string; body: string }) {
  return (
    <div>
      <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  );
}

type ScanResultViewProps = {
  report: ScanResultReport;
  eyebrow?: string;
  backTo?: { to: "/" | "/reports" | "/projects" | "/scan" | "/history" | "/settings" | "/results" | "/login"; label: string };
  onDelete?: () => void;
  primaryActionLabel?: string;
};

export function ScanResultView({
  report,
  eyebrow = "Assessment · Results",
  backTo = { to: "/", label: "Back to Dashboard" },
  onDelete,
  primaryActionLabel = "Run Another Scan",
}: ScanResultViewProps) {
  const { openStartScan } = useScanWorkflow();

  const meta = useMemo(
    () => [
      { k: "Report ID", v: report.id },
      { k: "Environment", v: report.env },
      { k: "Application Type", v: report.applicationType },
      { k: "Connection", v: report.connectionMethod },
      { k: "Profile", v: report.profile },
      { k: "Scan Time", v: report.scanTime },
      { k: "Duration", v: report.elapsedLabel },
    ],
    [report],
  );

  const timeline = useMemo(() => buildReportTimeline(report), [report]);
  const summary = useMemo(() => executiveSummaryText(report), [report]);

  return (
    <>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            {eyebrow}
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{report.projectName}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {report.profile} completed · overall score {report.score}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => mockExportReport(report, "PDF")}
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Download className="h-4 w-4" /> Export PDF
          </button>
          <button
            type="button"
            onClick={() => mockExportReport(report, "JSON")}
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <FileJson className="h-4 w-4" /> Export JSON
          </button>
          <button
            type="button"
            onClick={() => mockExportReport(report, "Share")}
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Share2 className="h-4 w-4" /> Share Report
          </button>
          {onDelete ? (
            <button
              type="button"
              onClick={onDelete}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" /> Delete
            </button>
          ) : null}
        </div>
      </div>

      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
        {meta.map((m) => (
          <div key={m.k} className="rounded-2xl border border-border bg-surface/40 px-4 py-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{m.k}</div>
            <div className="mt-1 truncate text-sm">{m.v}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[280px_1fr]">
        <Card className="h-fit">
          <div className="flex flex-col items-center py-2">
            <ScoreRing score={report.score} size={168} strokeWidth={9} label="Security Score" />
            <Chip tone={riskTone(report.riskLevel)} className="mt-4">
              Grade {report.grade} · {report.riskLevel} risk
            </Chip>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-2 border-t border-border pt-4">
            {[
              { k: "Critical", v: report.summary.critical, tone: "danger" as const },
              { k: "High", v: report.summary.high, tone: "danger" as const },
              { k: "Medium", v: report.summary.medium, tone: "warning" as const },
              { k: "Low", v: report.summary.low, tone: "info" as const },
            ].map((s) => (
              <div key={s.k} className="rounded-2xl border border-border bg-elevated/30 px-3 py-2.5">
                <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  <StatusDot tone={s.tone} /> {s.k}
                </div>
                <div className="mt-1 font-mono text-lg">{s.v}</div>
              </div>
            ))}
          </div>

          <div className="mt-3 rounded-2xl border border-border bg-elevated/30 px-3 py-2.5">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              Passed Tests
            </div>
            <div className="mt-1 font-mono text-lg">
              {report.summary.passed}
              <span className="text-sm text-muted-foreground"> / {report.summary.totalTests}</span>
            </div>
          </div>
        </Card>

        <div className="space-y-5">
          <Card>
            <SectionHeader eyebrow="Executive Summary" title="Assessment overview" />
            <p className="text-sm leading-relaxed text-muted-foreground">{summary}</p>
          </Card>

          <Card>
            <SectionHeader
              eyebrow="Findings"
              title="Security findings"
              action={
                <Chip tone="muted">
                  <ShieldAlert className="h-3 w-3" /> {report.findings.length} open items
                </Chip>
              }
            />
            <Accordion type="multiple" className="space-y-2">
              {report.findings.map((f) => (
                <AccordionItem
                  key={f.id}
                  value={f.id}
                  className="overflow-hidden rounded-2xl border border-border border-b-0 bg-surface/40 px-4"
                >
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2 pr-3 text-left">
                      <span className="text-sm font-medium">{f.title}</span>
                      <Chip tone={severityTone(f.severity)}>{f.severity}</Chip>
                      <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                        {f.category}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pb-4">
                    <FindingBlock label="Description" body={f.description} />
                    <FindingBlock label="Impact" body={f.impact} />
                    <FindingBlock label="Recommendation" body={f.recommendation} />
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                        Status
                      </span>
                      <Chip tone={f.status === "Open" ? "warning" : "muted"}>{f.status}</Chip>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Card>

          <Card>
            <SectionHeader eyebrow="Posture" title="Security score breakdown" />
            <div className="space-y-4">
              {report.breakdown.map((b) => (
                <div key={b.label}>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span>{b.label}</span>
                    <span className="font-mono tabular-nums text-muted-foreground">{b.score}</span>
                  </div>
                  <Progress
                    value={b.score}
                    className="h-1.5 rounded-full bg-hover [&>div]:rounded-full [&>div]:bg-foreground"
                  />
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionHeader eyebrow="Remediation" title="Prioritized recommendations" />
            <ul className="space-y-2">
              {report.recommendations.map((r) => (
                <li
                  key={r.text}
                  className="flex items-start gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3"
                >
                  <Chip
                    tone={r.priority === "P0" ? "danger" : r.priority === "P1" ? "warning" : "muted"}
                    className="mt-0.5 shrink-0"
                  >
                    {r.priority}
                  </Chip>
                  <div className="flex min-w-0 flex-1 items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                    <span className="text-sm">{r.text}</span>
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <SectionHeader eyebrow="Timeline" title="Scan timeline" />
            <ol className="space-y-3">
              {timeline.map((item, i) => (
                <li
                  key={`${item.t}-${item.l}`}
                  className="flex items-start gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3"
                >
                  <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-foreground/70" />
                  <div className="min-w-0 flex-1">
                    <div className="font-mono text-[11px] text-muted-foreground">{item.t}</div>
                    <div className="mt-0.5 text-sm">{item.l}</div>
                  </div>
                  {i === timeline.length - 1 ? <Chip tone="success">Complete</Chip> : null}
                </li>
              ))}
            </ol>
          </Card>

          <Card>
            <SectionHeader eyebrow="Metadata" title="Scan metadata" />
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { k: "Project", v: report.projectName },
                { k: "Report ID", v: report.id },
                { k: "Environment", v: report.env },
                { k: "Application Type", v: report.applicationType },
                { k: "Assessment Profile", v: report.profile },
                { k: "Connection Method", v: report.connectionMethod },
                { k: "Completed", v: report.scanTime },
                { k: "Duration", v: report.elapsedLabel },
                { k: "Overall Score", v: String(report.score) },
                { k: "Risk Level", v: report.riskLevel },
              ].map((m) => (
                <div key={m.k} className="rounded-2xl border border-border bg-elevated/30 px-4 py-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    {m.k}
                  </div>
                  <div className="mt-1 text-sm">{m.v}</div>
                </div>
              ))}
            </div>
          </Card>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => openStartScan()}
              className="inline-flex items-center gap-2 rounded-2xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
            >
              <Play className="h-4 w-4" strokeWidth={2.25} />
              {primaryActionLabel}
            </button>
            <Link
              to={backTo.to}
              className={cn(
                "inline-flex items-center gap-2 rounded-2xl border border-border bg-surface/50 px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-hover",
              )}
            >
              <ArrowLeft className="h-4 w-4" />
              {backTo.label}
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
