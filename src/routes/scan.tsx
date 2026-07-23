import { useEffect, useMemo, useRef, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card, Chip, ScoreRing, SectionHeader, StatusDot } from "@/components/ui-primitives";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import {
  clearScanSession,
  loadScanSession,
  type ActiveScanSession,
  type ScanAssessment,
  type ScanLogLine,
} from "@/lib/projects";
import { buildScanResult, saveScanResult } from "@/lib/scan-results";
import { addReport } from "@/lib/reports-store";
import { pushNotification } from "@/lib/notifications-store";
import { requireAuth } from "@/lib/auth";
import { CheckCircle2, Clock, Loader2, Pause, Play, ShieldAlert, Terminal, ChevronRight } from "lucide-react";

export const Route = createFileRoute("/scan")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Live Scan · AI Shield" },
      { name: "description", content: "Real-time AI security assessment in progress." },
      { property: "og:title", content: "Live Scan · AI Shield" },
      { property: "og:description", content: "Real-time AI security assessment in progress." },
    ],
  }),
  component: ScanPage,
});

function formatElapsed(ms: number) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const s = (total % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function formatLogTime(ms: number) {
  const total = Math.max(0, ms / 1000);
  const m = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const s = (total % 60).toFixed(2).padStart(5, "0");
  return `${m}:${s}`;
}

function gradeFor(score: number) {
  if (score >= 90) return "A";
  if (score >= 85) return "A-";
  if (score >= 80) return "B+";
  if (score >= 70) return "B";
  return "C";
}

function ScanPage() {
  const navigate = useNavigate();
  const { openStartScan } = useScanWorkflow();
  const [session, setSession] = useState<ActiveScanSession | null>(() => loadScanSession());
  const [assessments, setAssessments] = useState<ScanAssessment[]>([]);
  const [logs, setLogs] = useState<ScanLogLine[]>([]);
  const [score, setScore] = useState(72);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [progress, setProgress] = useState(0);
  const [complete, setComplete] = useState(false);
  const startedRef = useRef(false);
  const timersRef = useRef<number[]>([]);
  const scoreRef = useRef(score);
  const elapsedRef = useRef(elapsedMs);

  useEffect(() => {
    scoreRef.current = score;
  }, [score]);

  useEffect(() => {
    elapsedRef.current = elapsedMs;
  }, [elapsedMs]);

  const doneCount = assessments.filter((a) => a.status === "done").length;
  const runningCount = assessments.filter((a) => a.status === "running").length;
  const eta = useMemo(() => {
    const remaining = Math.max(0, assessments.length - doneCount - (runningCount ? 0.35 : 0));
    return formatElapsed(remaining * 2200);
  }, [assessments.length, doneCount, runningCount]);

  useEffect(() => {
    function hydrate(current: ActiveScanSession | null) {
      setSession(current);
      if (!current) {
        setAssessments([]);
        setLogs([]);
        setScore(72);
        setProgress(0);
        setElapsedMs(0);
        setComplete(false);
        startedRef.current = false;
        return;
      }

      timersRef.current.forEach((id) => {
        window.clearTimeout(id);
        window.clearInterval(id);
      });
      timersRef.current = [];
      startedRef.current = false;

      setAssessments(
        current.assessments.map((name) => ({
          name,
          status: "queued" as const,
          severity: "muted" as const,
          time: "—",
          findings: 0,
        })),
      );
      setLogs([
        { t: "00:00.12", l: `→ Bootstrapping scan runtime · workspace=aishield-prod` },
        { t: "00:00.48", l: `✓ Target reachable · ${current.projectName}@${current.env} (94ms)` },
        { t: "00:00.91", l: `→ Profile ${current.profile} · ${current.assessments.length} assessments` },
      ]);
      setScore(72);
      setProgress(0);
      setElapsedMs(0);
      setComplete(false);
    }

    hydrate(loadScanSession());

    const onStarted = (event: Event) => {
      const detail = (event as CustomEvent<ActiveScanSession>).detail;
      hydrate(detail ?? loadScanSession());
    };
    window.addEventListener("ais-scan-started", onStarted);
    return () => window.removeEventListener("ais-scan-started", onStarted);
  }, []);

  useEffect(() => {
    if (!session || startedRef.current || assessments.length === 0) return;
    startedRef.current = true;

    const tick = window.setInterval(() => {
      setElapsedMs(Date.now() - session.startedAt);
    }, 250);
    timersRef.current.push(tick);

    const STEP_MS = 1800;
    session.assessments.forEach((name, index) => {
      const startAt = 400 + index * STEP_MS;
      const finishAt = startAt + STEP_MS - 200;

      const startTimer = window.setTimeout(() => {
        setAssessments((prev) =>
          prev.map((a, i) =>
            i === index
              ? { ...a, status: "running", severity: "info", time: "—" }
              : a,
          ),
        );
        setLogs((prev) => [
          ...prev,
          {
            t: formatLogTime(startAt),
            l: `→ Assessment[${index + 1}/${session.assessments.length}] ${slug(name)} · probing`,
          },
        ]);
        setProgress(Math.round(((index + 0.35) / session.assessments.length) * 100));
      }, startAt);

      const finishTimer = window.setTimeout(() => {
        const findings = Math.random() < 0.35 ? 1 + Math.floor(Math.random() * 2) : 0;
        const duration = (1.1 + Math.random() * 2.2).toFixed(2);
        const severity = findings === 0 ? "success" : findings === 1 ? "info" : "warning";
        setAssessments((prev) =>
          prev.map((a, i) =>
            i === index
              ? {
                  ...a,
                  status: "done",
                  severity,
                  time: `${duration}s`,
                  findings,
                }
              : a,
          ),
        );
        setLogs((prev) => [
          ...prev,
          {
            t: formatLogTime(finishAt),
            l:
              findings > 0
                ? `! ${slug(name)} · ${findings} finding${findings > 1 ? "s" : ""} (${severity})`
                : `✓ ${slug(name)} · 0 findings · ${duration}s`,
          },
        ]);
        setScore((s) => Math.min(98, s + (findings === 0 ? 3 : 1)));
        setProgress(Math.round(((index + 1) / session.assessments.length) * 100));

        if (index === session.assessments.length - 1) {
          const doneTimer = window.setTimeout(() => {
            setComplete(true);
            setProgress(100);
            setLogs((prev) => [
              ...prev,
              { t: formatLogTime(finishAt + 400), l: "✓ Composite assessment complete · writing report artifact" },
            ]);
            const finalScore = scoreRef.current;
            const result = buildScanResult(session, finalScore, elapsedRef.current || finishAt + 400);
            saveScanResult(result);
            addReport(result);
            pushNotification({
              title: "Scan Completed",
              description: `Security assessment completed for ${result.projectName}.`,
              category: "security",
              severity: "success",
            });
            if (result.riskLevel === "High" || result.summary.critical > 0) {
              const critical = result.findings.find((f) => f.severity === "critical");
              pushNotification({
                title: "High Risk Detected",
                description: critical
                  ? `Critical ${critical.title} vulnerability detected.`
                  : `Elevated security risk detected on ${result.projectName}.`,
                category: "security",
                severity: "danger",
              });
            }
            clearScanSession();
            window.setTimeout(() => {
              void navigate({ to: "/results" });
            }, 1200);
          }, 600);
          timersRef.current.push(doneTimer);
        }
      }, finishAt);

      timersRef.current.push(startTimer, finishTimer);
    });

    return () => {
      timersRef.current.forEach((id) => {
        window.clearTimeout(id);
        window.clearInterval(id);
      });
      timersRef.current = [];
    };
  }, [session, assessments.length, navigate]);

  if (!session) {
    return (
      <AppShell>
        <Card className="mx-auto max-w-lg !p-8 text-center">
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Assessment
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">No scan in progress</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure a security assessment to begin live progress tracking.
          </p>
          <button
            type="button"
            onClick={() => openStartScan()}
            className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
          >
            <Play className="h-4 w-4" strokeWidth={2.25} />
            Start Security Assessment
          </button>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-info opacity-60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-info" />
            </span>
            Scan · {complete ? "complete" : "in progress"}
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {session.projectName} · {session.env}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {session.profile} · {session.applicationType} · initiated by Advith
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Pause className="h-4 w-4" /> Pause
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl bg-destructive/90 px-3 py-2 text-sm font-medium text-white hover:bg-destructive"
          >
            Abort
          </button>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_1.4fr]">
        <Card>
          <div className="flex flex-col items-center py-6">
            <ScoreRing score={score} size={220} strokeWidth={10} label={complete ? "Final" : "Interim"} />
            <div className="mt-6 grid w-full grid-cols-3 gap-2 border-t border-border pt-5">
              {[
                { k: "Grade", v: gradeFor(score) },
                { k: "Elapsed", v: formatElapsed(elapsedMs) },
                { k: "ETA", v: complete ? "00:00" : eta },
              ].map((s) => (
                <div key={s.k} className="text-center">
                  <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{s.k}</div>
                  <div className="font-mono text-base">{s.v}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-2 rounded-2xl border border-border bg-elevated/30 p-4">
            <div className="mb-2 flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-mono tabular-nums">{progress}%</span>
            </div>
            <div className="relative h-1.5 overflow-hidden rounded-full bg-hover">
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-foreground transition-[width] duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
              <div
                className="absolute inset-y-0 left-0 animate-pulse rounded-full bg-foreground/40 blur-sm transition-[width] duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="mt-3 font-mono text-[11px] text-muted-foreground">
              {doneCount} of {assessments.length} assessments complete
              {runningCount ? " · 1 running" : complete ? " · finished" : ""}
            </div>
          </div>
        </Card>

        <div className="flex flex-col gap-5">
          <Card>
            <SectionHeader eyebrow="Timeline" title="Assessments" />
            <ul className="space-y-2">
              {assessments.map((a) => (
                <li
                  key={a.name}
                  className="group flex items-center gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3 transition-colors hover:bg-hover/40"
                >
                  <div className="grid h-9 w-9 place-items-center rounded-xl bg-elevated">
                    {a.status === "done" ? (
                      <CheckCircle2 className="h-4 w-4 text-success" strokeWidth={1.75} />
                    ) : a.status === "running" ? (
                      <Loader2 className="h-4 w-4 animate-spin text-info" />
                    ) : (
                      <Clock className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm">{a.name}</span>
                      {a.findings > 0 && (
                        <Chip tone={a.severity === "warning" ? "warning" : "info"}>
                          <ShieldAlert className="h-2.5 w-2.5" /> {a.findings}
                        </Chip>
                      )}
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                      <StatusDot tone={a.severity} />
                      <span className="capitalize">{a.status === "done" ? "completed" : a.status}</span>
                      <span>·</span>
                      <span>{a.time}</span>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </li>
              ))}
            </ul>
          </Card>

          <Card className="!p-0 overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-muted-foreground" />
                <span className="font-mono text-xs text-muted-foreground">runtime.log</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-destructive/70" />
                <span className="h-2 w-2 rounded-full bg-warning/70" />
                <span className="h-2 w-2 rounded-full bg-success/70" />
              </div>
            </div>
            <div className="max-h-72 overflow-auto p-5 font-mono text-[11.5px] leading-relaxed">
              {logs.map((l, i) => (
                <div key={`${l.t}-${i}`} className="flex gap-4">
                  <span className="w-16 shrink-0 text-muted-foreground">{l.t}</span>
                  <span
                    className={
                      l.l.startsWith("!")
                        ? "text-warning"
                        : l.l.startsWith("✓")
                          ? "text-success"
                          : "text-foreground/90"
                    }
                  >
                    {l.l}
                  </span>
                </div>
              ))}
              {!complete ? (
                <div className="mt-1 flex gap-4">
                  <span className="w-16 text-muted-foreground">{formatLogTime(elapsedMs)}</span>
                  <span className="text-foreground/60">
                    → analyzing response distribution
                    <span className="ml-1 inline-block h-3 w-1.5 translate-y-0.5 animate-pulse bg-foreground" />
                  </span>
                </div>
              ) : null}
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

function slug(name: string) {
  return name.toLowerCase().replace(/\s+/g, "-");
}
