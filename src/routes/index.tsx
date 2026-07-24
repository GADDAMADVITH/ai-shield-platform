import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowUpRight,
  ArrowRight,
  Sparkles,
  Play,
  MoreHorizontal,
  TrendingUp,
  TrendingDown,
  Radar,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card, SectionHeader, ScoreRing, Sparkline, Chip, StatusDot } from "@/components/ui-primitives";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import { requireAuth } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";
import {
  getDashboardOverview,
  getDashboardRecent,
  getDashboardStatistics,
} from "@/lib/api/dashboard";
import type {
  DashboardOverview,
  DashboardRecentScan,
  DashboardStatistics,
} from "@/lib/api/types";
import { listProjects } from "@/lib/api/projects";
import type { BackendProject } from "@/lib/api/types";

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Dashboard · AI Shield" },
      {
        name: "description",
        content: "Live security posture, telemetry, and threat surface for your AI systems.",
      },
      { property: "og:title", content: "AI Shield Dashboard" },
      {
        property: "og:description",
        content: "Live security posture and threat telemetry for AI-native teams.",
      },
    ],
  }),
  component: Dashboard,
});

function relativeLabel(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.round(ms / 60_000));
  if (mins < 60) return `${mins}m`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours}h`;
  return `${Math.round(hours / 24)}d`;
}

function Dashboard() {
  const { openStartScan } = useScanWorkflow();
  const { user } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [stats, setStats] = useState<DashboardStatistics | null>(null);
  const [recent, setRecent] = useState<DashboardRecentScan[]>([]);
  const [projects, setProjects] = useState<BackendProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [ov, st, rec, proj] = await Promise.all([
          getDashboardOverview(),
          getDashboardStatistics(),
          getDashboardRecent(8),
          listProjects(1, 8),
        ]);
        if (cancelled) return;
        setOverview(ov);
        setStats(st);
        setRecent(rec.items);
        setProjects(proj.items);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const score = Math.round(overview?.average_security_score ?? 0);
  const successRate =
    overview && overview.total_scans > 0
      ? ((overview.successful_scans / overview.total_scans) * 100).toFixed(1)
      : "—";

  const metrics = useMemo(() => {
    const ov = overview;
    if (!ov) {
      return [
        { label: "Security Score", value: "—", delta: "—", tone: "muted" as const, spark: [0] },
        { label: "Projects Monitored", value: "—", delta: "—", tone: "info" as const, spark: [0] },
        { label: "Total Scans", value: "—", delta: "—", tone: "info" as const, spark: [0] },
        { label: "Critical Issues", value: "—", delta: "—", tone: "muted" as const, spark: [0] },
        { label: "Success Rate", value: "—", delta: "—", tone: "muted" as const, spark: [0] },
        { label: "Avg. Risk", value: "—", delta: "—", tone: "muted" as const, spark: [0] },
      ];
    }
    return [
      {
        label: "Security Score",
        value: String(Math.round(ov.average_security_score)),
        delta: ov.overall_security_posture,
        tone: "success" as const,
        spark: [60, 65, 70, 72, 75, 80, 85, Math.round(ov.average_security_score)],
        mono: true,
      },
      {
        label: "Projects Monitored",
        value: String(ov.total_projects),
        delta: `${ov.total_projects}`,
        tone: "info" as const,
        spark: [1, 2, 2, 3, 4, 5, 6, ov.total_projects || 1],
      },
      {
        label: "Total Scans",
        value: String(ov.total_scans),
        delta: `${ov.successful_scans} ok`,
        tone: "info" as const,
        spark: [2, 4, 6, 8, 10, 12, 14, ov.total_scans || 1],
      },
      {
        label: "Critical Issues",
        value: String(ov.critical_findings),
        delta: `${ov.high_findings} high`,
        tone: ov.critical_findings > 0 ? ("warning" as const) : ("success" as const),
        spark: [8, 7, 6, 5, 4, 3, 2, ov.critical_findings],
      },
      {
        label: "Success Rate",
        value: successRate === "—" ? "—" : `${successRate}%`,
        delta: `${ov.failed_scans} failed`,
        tone: "success" as const,
        spark: [90, 92, 94, 95, 96, 97, 98, Number(successRate) || 0],
      },
      {
        label: "Avg. Risk",
        value: String(Math.round(ov.average_risk_score)),
        delta: ov.overall_severity,
        tone: "muted" as const,
        spark: [40, 35, 30, 28, 25, 22, 20, Math.round(ov.average_risk_score)],
      },
    ];
  }, [overview, successRate]);

  const severityRows = useMemo(() => {
    const dist = stats?.severity_distribution;
    const total = Math.max(
      1,
      (dist?.critical ?? 0) +
        (dist?.high ?? 0) +
        (dist?.medium ?? 0) +
        (dist?.low ?? 0) +
        (dist?.info ?? 0),
    );
    return [
      { k: "Critical", v: dist?.critical ?? 0, tone: "bg-destructive" },
      { k: "High", v: dist?.high ?? 0, tone: "bg-warning" },
      { k: "Medium", v: dist?.medium ?? 0, tone: "bg-info" },
      { k: "Low", v: dist?.low ?? 0, tone: "bg-success" },
    ].map((r) => ({ ...r, pct: Math.round((r.v / total) * 100) }));
  }, [stats]);

  const trendData =
    stats?.risk.risk_trend?.map((p) => p.average_risk_score) ??
    [18, 22, 20, 25, 30, 28, 24, 22, 20, 18, 16, 14];

  const activity =
    overview?.latest_activity?.map((a) => ({
      t: relativeLabel(a.created_at),
      title:
        a.status === "completed"
          ? `Scan completed · ${a.total_findings} finding(s)`
          : `Scan ${a.status}`,
      proj: a.project_name ?? "project",
      sev:
        a.overall_risk_score >= 75
          ? "danger"
          : a.overall_risk_score >= 40
            ? "warning"
            : a.status === "completed"
              ? "success"
              : "info",
      status:
        a.overall_risk_score >= 75
          ? "Critical"
          : a.total_findings > 0
            ? "Review"
            : "Passed",
    })) ?? [];

  return (
    <AppShell>
      <section className="animate-float-in">
        <Card className="overflow-hidden p-0">
          <div className="grid gap-0 md:grid-cols-[1.4fr_1fr]">
            <div className="p-8 md:p-10">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-hover/50 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                <Sparkles className="h-3 w-3" />{" "}
                {overview?.overall_security_posture
                  ? `${overview.overall_security_posture} posture`
                  : "Security posture"}
              </div>
              <h1 className="text-3xl font-semibold tracking-tight md:text-[2.4rem] md:leading-[1.1]">
                Welcome back, {user?.name ?? "there"}.
                <br />
                <span className="text-muted-foreground">
                  {loading
                    ? "Loading live telemetry…"
                    : overview && overview.critical_findings === 0
                      ? "Your systems look stable."
                      : "Review open findings when ready."}
                </span>
              </h1>
              <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground">
                {error
                  ? error
                  : overview
                    ? `${overview.total_projects} project(s), ${overview.total_scans} scan(s), ${overview.total_findings} finding(s) across your workspace.`
                    : "Connect a project and run a scan to populate this dashboard."}
              </p>

              <div className="mt-7 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => openStartScan()}
                  className="inline-flex items-center gap-2 rounded-2xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
                >
                  <Play className="h-4 w-4" strokeWidth={2.25} />
                  Run new scan
                </button>
                <Link
                  to="/reports"
                  className="inline-flex items-center gap-2 rounded-2xl border border-border bg-surface/50 px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-hover"
                >
                  View reports <ArrowUpRight className="h-4 w-4" />
                </Link>
              </div>

              <div className="mt-8 grid grid-cols-3 gap-2 border-t border-border pt-6">
                {[
                  { k: "Successful", v: String(overview?.successful_scans ?? 0) },
                  { k: "Failed", v: String(overview?.failed_scans ?? 0) },
                  { k: "Findings", v: String(overview?.total_findings ?? 0) },
                ].map((s) => (
                  <div key={s.k}>
                    <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                      {s.k}
                    </div>
                    <div className="font-mono text-lg tracking-tight">{s.v}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative flex items-center justify-center border-border bg-gradient-to-br from-elevated/40 to-transparent p-8 md:border-l">
              <div className="pointer-events-none absolute inset-0 grid-noise" />
              <div className="relative flex flex-col items-center">
                <div className="relative">
                  <div className="absolute inset-0 -m-3 rounded-full bg-foreground/5 blur-xl" />
                  <ScoreRing score={score} size={200} strokeWidth={9} label="Composite" />
                </div>
                <div className="mt-6 flex items-center gap-2 rounded-full border border-border bg-surface/60 px-3 py-1.5 backdrop-blur-xl">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                  </span>
                  <span className="font-mono text-[11px] tracking-wide text-foreground">
                    {overview?.overall_security_posture ?? "Awaiting scans"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {metrics.map((m, i) => {
          const positive = String(m.delta).startsWith("+") || m.tone === "success";
          return (
            <Card key={m.label} className="animate-float-in !p-4" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {m.label}
                </span>
                <MoreHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="flex items-end justify-between gap-2">
                <div className="font-mono text-[1.7rem] font-medium leading-none tracking-tight">
                  {m.value}
                </div>
                <div
                  className={`inline-flex items-center gap-1 font-mono text-[10px] ${
                    m.tone === "success" ? "text-success" : "text-muted-foreground"
                  }`}
                >
                  {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {m.delta}
                </div>
              </div>
              <div className="mt-3">
                <Sparkline data={m.spark} tone={m.tone === "success" ? "success" : "foreground"} />
              </div>
            </Card>
          );
        })}
      </section>

      <section className="mt-6 grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <Card>
          <SectionHeader eyebrow="Analytics" title="Risk trend" />
          <TrendChart data={trendData} />
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 text-xs">
            {[
              { k: "Findings", v: String(overview?.total_findings ?? 0), tone: "text-foreground" },
              {
                k: "Critical",
                v: String(overview?.critical_findings ?? 0),
                tone: "text-destructive",
              },
              { k: "High", v: String(overview?.high_findings ?? 0), tone: "text-warning" },
            ].map((k) => (
              <div key={k.k}>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {k.k}
                </div>
                <div className={`font-mono text-lg ${k.tone}`}>{k.v}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeader
            eyebrow="Live telemetry"
            title="Recent activity"
            action={
              <Link
                to="/history"
                className="font-mono text-[11px] text-muted-foreground hover:text-foreground"
              >
                View all <ArrowRight className="inline h-3 w-3" />
              </Link>
            }
          />
          <ul className="-mx-2 space-y-1">
            {(activity.length ? activity : recent.map((r) => ({
              t: relativeLabel(r.created_at),
              title: `${r.project_name ?? "Scan"} · ${r.status}`,
              proj: r.profile,
              sev: (r.critical > 0 ? "danger" : r.total_findings > 0 ? "warning" : "success") as string,
              status: r.status,
            }))).slice(0, 6).map((a) => (
              <li
                key={`${a.title}-${a.t}-${a.proj}`}
                className="group flex items-start gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-hover/50"
              >
                <div className="mt-1.5">
                  <StatusDot tone={a.sev as "info" | "success" | "warning" | "danger"} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{a.title}</div>
                  <div className="mt-0.5 flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                    <span>{a.proj}</span>
                    <span>·</span>
                    <span>{a.t} ago</span>
                  </div>
                </div>
                <Chip tone={a.sev as "info" | "success" | "warning" | "danger"}>{a.status}</Chip>
              </li>
            ))}
            {!loading && activity.length === 0 && recent.length === 0 ? (
              <li className="px-2 py-6 text-sm text-muted-foreground">No scans yet.</li>
            ) : null}
          </ul>
        </Card>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-3">
        <Card>
          <SectionHeader eyebrow="Risk" title="Severity distribution" />
          <div className="space-y-3">
            {severityRows.map((r) => (
              <div key={r.k}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{r.k}</span>
                  <span className="font-mono tabular-nums text-foreground">{r.v}</span>
                </div>
                <div className="relative h-1.5 overflow-hidden rounded-full bg-hover">
                  <div
                    className={`h-full rounded-full ${r.tone}`}
                    style={{
                      width: `${r.pct}%`,
                      transition: "width 900ms cubic-bezier(0.16,1,0.3,1)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <SectionHeader
            eyebrow="Fleet"
            title="Project health"
            action={
              <Link
                to="/projects"
                className="font-mono text-[11px] text-muted-foreground hover:text-foreground"
              >
                Open projects <ArrowRight className="inline h-3 w-3" />
              </Link>
            }
          />
          <div className="grid gap-2 md:grid-cols-2">
            {projects.length === 0 && !loading ? (
              <div className="col-span-2 rounded-2xl border border-dashed border-border p-6 text-sm text-muted-foreground">
                No projects yet. Create one to start scanning.
              </div>
            ) : null}
            {projects.map((p) => (
              <div
                key={p.id}
                className="group flex items-center gap-3 rounded-2xl border border-border bg-surface/40 p-3 transition-colors hover:bg-hover/40"
              >
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-elevated">
                  <Radar className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-mono text-sm">{p.name}</span>
                    <StatusDot
                      tone={
                        p.status === "connected"
                          ? "success"
                          : p.status === "error"
                            ? "danger"
                            : "warning"
                      }
                    />
                  </div>
                  <div className="truncate text-[11px] text-muted-foreground">
                    {p.application_type} · {p.environment}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-sm capitalize tabular-nums">{p.status}</div>
                  <div className="font-mono text-[10px] text-muted-foreground">
                    {p.connection_method}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </AppShell>
  );
}

function TrendChart({ data }: { data: number[] }) {
  const series = data.length > 1 ? data : [0, 0];
  const w = 640;
  const h = 180;
  const max = Math.max(...series, 1);
  const step = w / (series.length - 1);
  const pts = series.map((v, i) => `${i * step},${h - (v / max) * (h - 16) - 8}`).join(" ");
  const area = `0,${h} ${pts} ${w},${h}`;
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${w} ${h}`} className="h-44 w-full">
        <defs>
          <linearGradient id="trendGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--foreground)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--foreground)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((y) => (
          <line
            key={y}
            x1="0"
            x2={w}
            y1={h * y}
            y2={h * y}
            stroke="var(--border)"
            strokeDasharray="2 4"
          />
        ))}
        <polygon points={area} fill="url(#trendGrad)" />
        <polyline
          points={pts}
          fill="none"
          stroke="var(--foreground)"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
