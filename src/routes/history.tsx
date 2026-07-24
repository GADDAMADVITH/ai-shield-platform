import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card, Chip } from "@/components/ui-primitives";
import { ChevronRight, Filter, Search } from "lucide-react";
import { requireAuth } from "@/lib/auth";
import { getScanHistory } from "@/lib/api/dashboard";
import type { ScanHistoryItem } from "@/lib/api/types";

export const Route = createFileRoute("/history")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Scan History · AI Shield" },
      { name: "description", content: "Complete audit trail of every AI security scan." },
      { property: "og:title", content: "Scan History · AI Shield" },
      { property: "og:description", content: "Complete audit trail of every AI security scan." },
    ],
  }),
  component: History,
});

function formatDuration(ms: number | null): string {
  if (ms == null) return "—";
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const s = (total % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusTone(status: string, score: number | null): "success" | "warning" | "danger" | "info" {
  if (status === "failed") return "danger";
  if (status === "completed" && (score ?? 100) < 70) return "danger";
  if (status === "completed" && (score ?? 100) < 85) return "warning";
  if (status === "completed") return "success";
  return "info";
}

function History() {
  const [rows, setRows] = useState<ScanHistoryItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const page = await getScanHistory({ page: 1, pageSize: 50, sort: "newest" });
        if (!cancelled) setRows(page.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load history");
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
    if (!q) return rows;
    return rows.filter(
      (r) =>
        r.id.toLowerCase().includes(q) ||
        (r.project_name ?? "").toLowerCase().includes(q) ||
        r.status.toLowerCase().includes(q),
    );
  }, [rows, search]);

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Audit
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Scan history</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search scans…"
              className="w-56 bg-transparent outline-none placeholder:text-muted-foreground"
            />
          </div>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Filter className="h-4 w-4" /> Filter
          </button>
        </div>
      </div>

      {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}

      <Card className="!p-0 overflow-hidden">
        <div className="grid grid-cols-[1.2fr_1.4fr_0.7fr_0.7fr_0.8fr_1fr_0.8fr_32px] gap-4 border-b border-border px-6 py-3 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          <span>Scan ID</span>
          <span>Project</span>
          <span>Score</span>
          <span>Findings</span>
          <span>Duration</span>
          <span>When</span>
          <span>Status</span>
          <span />
        </div>
        <ul>
          {loading ? (
            <li className="px-6 py-8 text-sm text-muted-foreground">Loading scan history…</li>
          ) : null}
          {!loading && filtered.length === 0 ? (
            <li className="px-6 py-8 text-sm text-muted-foreground">No scans found.</li>
          ) : null}
          {filtered.map((r) => (
            <li
              key={r.id}
              className="group grid grid-cols-[1.2fr_1.4fr_0.7fr_0.7fr_0.8fr_1fr_0.8fr_32px] items-center gap-4 border-b border-border/50 px-6 py-3.5 text-sm transition-colors last:border-b-0 hover:bg-hover/40"
            >
              <span className="truncate font-mono text-[12.5px] text-muted-foreground">{r.id}</span>
              <div className="min-w-0">
                <div className="truncate font-mono text-[13px]">{r.project_name ?? "—"}</div>
                <div className="truncate text-[11px] text-muted-foreground">
                  {r.environment ?? "—"}
                </div>
              </div>
              <span className="font-mono tabular-nums">
                {r.overall_security_score != null ? Math.round(r.overall_security_score) : "—"}
              </span>
              <span className="font-mono tabular-nums text-muted-foreground">{r.total_findings}</span>
              <span className="font-mono tabular-nums text-muted-foreground">
                {formatDuration(r.execution_time_ms)}
              </span>
              <span className="text-muted-foreground">{formatWhen(r.created_at)}</span>
              <span>
                <Chip tone={statusTone(r.status, r.overall_security_score)}>{r.status}</Chip>
              </span>
              <span className="justify-self-end text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
                <ChevronRight className="h-4 w-4" />
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </AppShell>
  );
}
