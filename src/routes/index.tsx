import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ShieldCheck,
  ArrowUpRight,
  ArrowRight,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Activity,
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

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Dashboard · AI Shield" },
      { name: "description", content: "Live security posture, telemetry, and threat surface for your AI systems." },
      { property: "og:title", content: "AI Shield Dashboard" },
      { property: "og:description", content: "Live security posture and threat telemetry for AI-native teams." },
    ],
  }),
  component: Dashboard,
});

const metrics = [
  { label: "Security Score", value: "94", delta: "+2.1", tone: "success" as const, spark: [70, 72, 74, 78, 82, 88, 91, 94], mono: true },
  { label: "Projects Monitored", value: "28", delta: "+3", tone: "info" as const, spark: [12, 14, 18, 20, 22, 24, 26, 28] },
  { label: "Scans (30d)", value: "1,284", delta: "+184", tone: "info" as const, spark: [80, 120, 100, 160, 180, 220, 240, 284] },
  { label: "Critical Issues", value: "3", delta: "-7", tone: "success" as const, spark: [12, 10, 9, 7, 6, 5, 4, 3] },
  { label: "Success Rate", value: "99.8%", delta: "+0.4", tone: "success" as const, spark: [96, 97, 97, 98, 98, 99, 99.5, 99.8] },
  { label: "Avg. Risk", value: "Low", delta: "Stable", tone: "muted" as const, spark: [30, 28, 26, 22, 20, 18, 18, 17] },
];

const activity = [
  { t: "2m", title: "Prompt-injection surface scan completed", proj: "knowledge-rag · production", sev: "info", status: "Passed" },
  { t: "14m", title: "Model exfiltration probe flagged 2 endpoints", proj: "dev-copilot", sev: "warning", status: "Review" },
  { t: "1h", title: "PII leakage assessment finished", proj: "support-chat", sev: "success", status: "Passed" },
  { t: "3h", title: "Jailbreak resilience regression", proj: "ops-agent", sev: "danger", status: "Critical" },
  { t: "6h", title: "Weekly compliance report generated", proj: "workspace · aishield-prod", sev: "info", status: "Signed" },
];

function Dashboard() {
  const { openStartScan } = useScanWorkflow();
  const { user } = useAuth();
  return (
    <AppShell>
      {/* Hero */}
      <section className="animate-float-in">
        <Card className="overflow-hidden p-0">
          <div className="grid gap-0 md:grid-cols-[1.4fr_1fr]">
            <div className="p-8 md:p-10">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-hover/50 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                <Sparkles className="h-3 w-3" /> Threat surface calm
              </div>
              <h1 className="text-3xl font-semibold tracking-tight md:text-[2.4rem] md:leading-[1.1]">
                Welcome back, {user?.name ?? "there"}.
                <br />
                <span className="text-muted-foreground">Your systems are secure.</span>
              </h1>
              <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground">
                No critical incidents in the last 72 hours. 28 projects under continuous
                observation across 4 environments — the next scheduled scan runs in 12 minutes.
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
                  { k: "Uptime", v: "99.98%" },
                  { k: "Coverage", v: "94.2%" },
                  { k: "MTTD", v: "1.4m" },
                ].map((s) => (
                  <div key={s.k}>
                    <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{s.k}</div>
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
                  <ScoreRing score={94} size={200} strokeWidth={9} label="Composite" />
                </div>
                <div className="mt-6 flex items-center gap-2 rounded-full border border-border bg-surface/60 px-3 py-1.5 backdrop-blur-xl">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                  </span>
                  <span className="font-mono text-[11px] tracking-wide text-foreground">All systems nominal</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* Metrics */}
      <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {metrics.map((m, i) => {
          const positive = m.delta.startsWith("+") || m.tone === "success";
          const negative = m.delta.startsWith("-") && m.label === "Critical Issues" ? false : m.delta.startsWith("-");
          return (
            <Card
              key={m.label}
              className="animate-float-in !p-4"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{m.label}</span>
                <MoreHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="flex items-end justify-between gap-2">
                <div className="font-mono text-[1.7rem] font-medium leading-none tracking-tight">{m.value}</div>
                <div
                  className={`inline-flex items-center gap-1 font-mono text-[10px] ${
                    m.tone === "success" ? "text-success" : "text-muted-foreground"
                  }`}
                >
                  {positive ? <TrendingUp className="h-3 w-3" /> : negative ? <TrendingDown className="h-3 w-3" /> : null}
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

      {/* Analytics + activity */}
      <section className="mt-6 grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <Card>
          <SectionHeader
            eyebrow="Analytics"
            title="Vulnerability trend"
            action={
              <div className="flex items-center gap-1 rounded-xl border border-border bg-hover/40 p-0.5 font-mono text-[10px] text-muted-foreground">
                {["24h", "7d", "30d", "90d"].map((t, i) => (
                  <button
                    key={t}
                    className={`rounded-lg px-2.5 py-1 ${i === 2 ? "bg-elevated text-foreground" : "hover:text-foreground"}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            }
          />
          <TrendChart />
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 text-xs">
            {[
              { k: "Detected", v: "312", tone: "text-foreground" },
              { k: "Resolved", v: "298", tone: "text-success" },
              { k: "Open", v: "14", tone: "text-warning" },
            ].map((k) => (
              <div key={k.k}>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{k.k}</div>
                <div className={`font-mono text-lg ${k.tone}`}>{k.v}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeader
            eyebrow="Live telemetry"
            title="Recent activity"
            action={<Link to="/history" className="font-mono text-[11px] text-muted-foreground hover:text-foreground">View all <ArrowRight className="inline h-3 w-3" /></Link>}
          />
          <ul className="-mx-2 space-y-1">
            {activity.map((a) => (
              <li key={a.title} className="group flex items-start gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-hover/50">
                <div className="mt-1.5">
                  <StatusDot tone={a.sev as any} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{a.title}</div>
                  <div className="mt-0.5 flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                    <span>{a.proj}</span>
                    <span>·</span>
                    <span>{a.t} ago</span>
                  </div>
                </div>
                <Chip tone={a.sev as any}>{a.status}</Chip>
              </li>
            ))}
          </ul>
        </Card>
      </section>

      {/* Distribution + assets */}
      <section className="mt-6 grid gap-5 lg:grid-cols-3">
        <Card>
          <SectionHeader eyebrow="Risk" title="Severity distribution" />
          <div className="space-y-3">
            {[
              { k: "Critical", v: 3, pct: 4, tone: "bg-destructive" },
              { k: "High", v: 11, pct: 14, tone: "bg-warning" },
              { k: "Medium", v: 42, pct: 54, tone: "bg-info" },
              { k: "Low", v: 22, pct: 28, tone: "bg-success" },
            ].map((r) => (
              <div key={r.k}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{r.k}</span>
                  <span className="font-mono tabular-nums text-foreground">{r.v}</span>
                </div>
                <div className="relative h-1.5 overflow-hidden rounded-full bg-hover">
                  <div
                    className={`h-full rounded-full ${r.tone}`}
                    style={{ width: `${r.pct}%`, transition: "width 900ms cubic-bezier(0.16,1,0.3,1)" }}
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
            action={<Link to="/projects" className="font-mono text-[11px] text-muted-foreground hover:text-foreground">Open projects <ArrowRight className="inline h-3 w-3" /></Link>}
          />
          <div className="grid gap-2 md:grid-cols-2">
            {[
              { name: "knowledge-rag", type: "RAG · GPT-4o", score: 96, tone: "success", scans: 128 },
              { name: "dev-copilot", type: "Agent · Claude 3.5", score: 82, tone: "warning", scans: 74 },
              { name: "support-chat", type: "Chat · Llama 3", score: 91, tone: "success", scans: 212 },
              { name: "ops-agent", type: "Autonomous · Multi-tool", score: 68, tone: "danger", scans: 41 },
            ].map((p) => (
              <div
                key={p.name}
                className="group flex items-center gap-3 rounded-2xl border border-border bg-surface/40 p-3 transition-colors hover:bg-hover/40"
              >
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-elevated">
                  <Radar className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-mono text-sm">{p.name}</span>
                    <StatusDot tone={p.tone as any} />
                  </div>
                  <div className="truncate text-[11px] text-muted-foreground">{p.type}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-lg tabular-nums">{p.score}</div>
                  <div className="font-mono text-[10px] text-muted-foreground">{p.scans} scans</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </AppShell>
  );
}

function TrendChart() {
  const data = [
    18, 22, 20, 25, 30, 28, 24, 32, 36, 30, 26, 22, 28, 34, 40, 36, 30, 26, 24, 20, 18, 16, 14, 12,
  ];
  const w = 640;
  const h = 180;
  const max = Math.max(...data);
  const step = w / (data.length - 1);
  const pts = data.map((v, i) => `${i * step},${h - (v / max) * (h - 16) - 8}`).join(" ");
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
          <line key={y} x1="0" x2={w} y1={h * y} y2={h * y} stroke="var(--border)" strokeDasharray="2 4" />
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
      <div className="mt-2 flex justify-between font-mono text-[10px] text-muted-foreground">
        {["Wk1", "Wk2", "Wk3", "Wk4"].map((w) => (
          <span key={w}>{w}</span>
        ))}
      </div>
    </div>
  );
}
