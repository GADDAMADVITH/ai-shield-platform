import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  Search,
  ChevronRight,
  Download,
  FileJson,
  Trash2,
  Play,
  FileText,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card, Chip } from "@/components/ui-primitives";
import { ConfirmDialog } from "@/components/settings/shared";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import { mockExportReport, riskTone } from "@/components/scan-result-view";
import {
  deleteReport,
  filterReports,
  loadReports,
  uniqueAppTypes,
  uniqueEnvs,
  uniqueRisks,
  type ReportSort,
} from "@/lib/reports-store";
import type { ScanResultReport } from "@/lib/scan-results";
import { selectContentClass, selectTriggerClass } from "@/components/settings/shared";
import { requireAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reports")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Reports · AI Shield" },
      { name: "description", content: "Executive-ready AI security reports and compliance artifacts." },
      { property: "og:title", content: "Reports · AI Shield" },
      { property: "og:description", content: "Executive-ready AI security reports and compliance artifacts." },
    ],
  }),
  component: Reports,
});

function Reports() {
  const { openStartScan } = useScanWorkflow();
  const [reports, setReports] = useState<ScanResultReport[]>(() => loadReports());
  const [search, setSearch] = useState("");
  const [env, setEnv] = useState("all");
  const [risk, setRisk] = useState("all");
  const [applicationType, setApplicationType] = useState("all");
  const [sort, setSort] = useState<ReportSort>("date-desc");
  const [pendingDelete, setPendingDelete] = useState<ScanResultReport | null>(null);

  const envs = useMemo(() => uniqueEnvs(reports), [reports]);
  const appTypes = useMemo(() => uniqueAppTypes(reports), [reports]);
  const risks = useMemo(() => uniqueRisks(reports), [reports]);

  const filtered = useMemo(
    () => filterReports(reports, { search, env, risk, applicationType, sort }),
    [reports, search, env, risk, applicationType, sort],
  );

  function confirmDelete() {
    if (!pendingDelete) return;
    const next = deleteReport(pendingDelete.id);
    setReports(next);
    toast.success("Report deleted", { description: pendingDelete.id });
    setPendingDelete(null);
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
        {hasAny ? (
          <button
            type="button"
            onClick={() => openStartScan()}
            className="inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
          >
            <Play className="h-4 w-4" strokeWidth={2.25} /> Run New Scan
          </button>
        ) : null}
      </div>

      {!hasAny ? (
        <Card className="flex flex-col items-center justify-center px-6 py-16 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-2xl border border-border bg-elevated">
            <FileText className="h-6 w-6 text-muted-foreground" strokeWidth={1.6} />
          </div>
          <h2 className="mt-5 text-lg font-semibold tracking-tight">No security reports yet.</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Run a scan to generate an executive-ready security report for your AI application.
          </p>
          <button
            type="button"
            onClick={() => openStartScan()}
            className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
          >
            <Play className="h-4 w-4" strokeWidth={2.25} />
            Run New Scan
          </button>
        </Card>
      ) : (
        <>
          <Card className="mb-5 !p-4">
            <div className="grid gap-3 lg:grid-cols-[1.4fr_repeat(4,minmax(0,1fr))]">
              <div className="flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm">
                <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by project name…"
                  className="w-full bg-transparent outline-none placeholder:text-muted-foreground"
                />
              </div>

              <FilterSelect
                label="Environment"
                value={env}
                onValueChange={setEnv}
                options={[
                  { value: "all", label: "All environments" },
                  ...envs.map((e) => ({ value: e, label: e })),
                ]}
              />
              <FilterSelect
                label="Risk Level"
                value={risk}
                onValueChange={setRisk}
                options={[
                  { value: "all", label: "All risk levels" },
                  ...risks.map((r) => ({ value: r, label: r })),
                ]}
              />
              <FilterSelect
                label="Application Type"
                value={applicationType}
                onValueChange={setApplicationType}
                options={[
                  { value: "all", label: "All types" },
                  ...appTypes.map((t) => ({ value: t, label: t })),
                ]}
              />
              <FilterSelect
                label="Sort"
                value={sort}
                onValueChange={(v) => setSort(v as ReportSort)}
                options={[
                  { value: "date-desc", label: "Date · newest" },
                  { value: "date-asc", label: "Date · oldest" },
                  { value: "score-desc", label: "Score · high to low" },
                  { value: "score-asc", label: "Score · low to high" },
                ]}
              />
            </div>
          </Card>

          {filtered.length === 0 ? (
            <Card className="px-6 py-12 text-center">
              <p className="text-sm text-muted-foreground">No reports match your filters.</p>
              <button
                type="button"
                onClick={() => {
                  setSearch("");
                  setEnv("all");
                  setRisk("all");
                  setApplicationType("all");
                  setSort("date-desc");
                }}
                className="mt-4 text-sm text-foreground underline-offset-4 hover:underline"
              >
                Clear filters
              </button>
            </Card>
          ) : (
            <Card className="!p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <div className="min-w-[980px]">
                  <div className="grid grid-cols-[1fr_1.2fr_1.3fr_0.9fr_1.1fr_0.7fr_0.9fr_1fr_88px] gap-3 border-b border-border px-6 py-3 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    <span>Report ID</span>
                    <span>Project</span>
                    <span>Application Type</span>
                    <span>Environment</span>
                    <span>Scan Date</span>
                    <span>Score</span>
                    <span>Risk</span>
                    <span>Profile</span>
                    <span />
                  </div>
                  <ul>
                    {filtered.map((r) => (
                      <li key={r.id} className="group border-b border-border/50 last:border-b-0">
                        <div className="grid grid-cols-[1fr_1.2fr_1.3fr_0.9fr_1.1fr_0.7fr_0.9fr_1fr_88px] items-center gap-3 px-6 py-3.5 text-sm transition-colors hover:bg-hover/40">
                          <Link
                            to="/reports/$reportId"
                            params={{ reportId: r.id }}
                            className="truncate font-mono text-[12.5px] text-muted-foreground hover:text-foreground"
                          >
                            {r.id}
                          </Link>
                          <Link
                            to="/reports/$reportId"
                            params={{ reportId: r.id }}
                            className="min-w-0 truncate font-mono text-[13px] hover:underline"
                          >
                            {r.projectName}
                          </Link>
                          <span className="truncate text-muted-foreground">{r.applicationType}</span>
                          <span className="truncate capitalize text-muted-foreground">{r.env}</span>
                          <span className="truncate text-muted-foreground">{r.scanTime}</span>
                          <span className="font-mono tabular-nums">{r.score}</span>
                          <span>
                            <Chip tone={riskTone(r.riskLevel)}>{r.riskLevel}</Chip>
                          </span>
                          <span className="truncate text-muted-foreground">{r.profile}</span>
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              title="Export PDF"
                              onClick={(e) => {
                                e.preventDefault();
                                mockExportReport(r, "PDF");
                              }}
                              className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground opacity-0 transition-opacity hover:bg-hover hover:text-foreground group-hover:opacity-100"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              title="Export JSON"
                              onClick={(e) => {
                                e.preventDefault();
                                mockExportReport(r, "JSON");
                              }}
                              className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground opacity-0 transition-opacity hover:bg-hover hover:text-foreground group-hover:opacity-100"
                            >
                              <FileJson className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              title="Delete report"
                              onClick={(e) => {
                                e.preventDefault();
                                setPendingDelete(r);
                              }}
                              className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground opacity-0 transition-opacity hover:bg-hover hover:text-destructive group-hover:opacity-100"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                            <Link
                              to="/reports/$reportId"
                              params={{ reportId: r.id }}
                              className={cn(
                                "grid h-8 w-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-hover hover:text-foreground",
                              )}
                            >
                              <ChevronRight className="h-4 w-4" />
                            </Link>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      <ConfirmDialog
        open={!!pendingDelete}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Delete report?"
        description={
          pendingDelete
            ? `Remove ${pendingDelete.id} (${pendingDelete.projectName}) from the reports library. This only updates local mock data.`
            : ""
        }
        confirmLabel="Delete report"
        destructive
        onConfirm={confirmDelete}
      />
    </AppShell>
  );
}

function FilterSelect({
  label,
  value,
  onValueChange,
  options,
}: {
  label: string;
  value: string;
  onValueChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <div className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </div>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className={cn(selectTriggerClass, "h-10")}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent className={selectContentClass}>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value} className="rounded-xl">
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
