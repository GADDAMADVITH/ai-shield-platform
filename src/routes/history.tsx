import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card, Chip } from "@/components/ui-primitives";
import { ChevronRight, Filter, Search } from "lucide-react";
import { requireAuth } from "@/lib/auth";

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

const rows = [
  { id: "scn_9f2a7e", proj: "knowledge-rag", env: "production", score: 94, findings: 3, duration: "02:41", when: "Today · 09:22", status: "passed" },
  { id: "scn_9f1b3c", proj: "dev-copilot", env: "staging", score: 82, findings: 7, duration: "03:12", when: "Today · 08:04", status: "review" },
  { id: "scn_9f0a2d", proj: "support-chat", env: "production", score: 91, findings: 2, duration: "01:58", when: "Yesterday · 22:11", status: "passed" },
  { id: "scn_9ef1a8", proj: "ops-agent", env: "production", score: 68, findings: 12, duration: "04:22", when: "Yesterday · 14:39", status: "critical" },
  { id: "scn_9ee0c1", proj: "embed-api", env: "development", score: 88, findings: 4, duration: "01:12", when: "Nov 27 · 11:02", status: "passed" },
  { id: "scn_9ed2f4", proj: "voice-realtime", env: "staging", score: 79, findings: 5, duration: "02:26", when: "Nov 26 · 16:44", status: "review" },
  { id: "scn_9ec8b2", proj: "knowledge-rag", env: "production", score: 92, findings: 3, duration: "02:18", when: "Nov 26 · 09:03", status: "passed" },
];

function History() {
  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Audit</div>
          <h1 className="text-2xl font-semibold tracking-tight">Scan history</h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input placeholder="Search scans…" className="w-56 bg-transparent outline-none placeholder:text-muted-foreground" />
          </div>
          <button className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground">
            <Filter className="h-4 w-4" /> Filter
          </button>
        </div>
      </div>

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
          {rows.map((r) => (
            <li
              key={r.id}
              className="group grid grid-cols-[1.2fr_1.4fr_0.7fr_0.7fr_0.8fr_1fr_0.8fr_32px] items-center gap-4 border-b border-border/50 px-6 py-3.5 text-sm transition-colors last:border-b-0 hover:bg-hover/40"
            >
              <span className="truncate font-mono text-[12.5px] text-muted-foreground">{r.id}</span>
              <div className="min-w-0">
                <div className="truncate font-mono text-[13px]">{r.proj}</div>
                <div className="truncate text-[11px] text-muted-foreground">{r.env}</div>
              </div>
              <span className="font-mono tabular-nums">{r.score}</span>
              <span className="font-mono tabular-nums text-muted-foreground">{r.findings}</span>
              <span className="font-mono tabular-nums text-muted-foreground">{r.duration}</span>
              <span className="text-muted-foreground">{r.when}</span>
              <span>
                <Chip
                  tone={r.status === "passed" ? "success" : r.status === "review" ? "warning" : "danger"}
                >
                  {r.status}
                </Chip>
              </span>
              <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100" />
            </li>
          ))}
        </ul>
      </Card>
    </AppShell>
  );
}
