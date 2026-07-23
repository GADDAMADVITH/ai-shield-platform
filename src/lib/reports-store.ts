import {
  buildScanResult,
  type ScanResultReport,
} from "@/lib/scan-results";
import type { ActiveScanSession } from "@/lib/projects";

const REPORTS_KEY = "ais-reports";

function session(
  partial: Omit<ActiveScanSession, "startedAt" | "assessments"> & {
    assessments?: string[];
    startedAt?: number;
  },
): ActiveScanSession {
  return {
    assessments: partial.assessments ?? [
      "Prompt Injection",
      "Jailbreak",
      "Prompt Leakage",
      "Sensitive Data Leakage",
      "Hallucination",
    ],
    startedAt: partial.startedAt ?? Date.now() - 180000,
    id: partial.id,
    projectId: partial.projectId,
    projectName: partial.projectName,
    env: partial.env,
    applicationType: partial.applicationType,
    connectionMethod: partial.connectionMethod,
    profile: partial.profile,
  };
}

function withCompletedAt(report: ScanResultReport, iso: string, scanTime: string): ScanResultReport {
  return { ...report, completedAt: iso, scanTime };
}

/** Seed library for first visit — mirrors demo projects and history. */
export function seedReports(): ScanResultReport[] {
  return [
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9f2a7e",
            projectId: "knowledge-rag",
            projectName: "knowledge-rag",
            env: "production",
            applicationType: "RAG / Document Q&A",
            connectionMethod: "REST API",
            profile: "Standard Scan",
            assessments: [
              "Prompt Injection",
              "Jailbreak",
              "Prompt Leakage",
              "Sensitive Data Leakage",
              "Hallucination",
              "Retrieval Manipulation",
              "Unauthorized Document Retrieval",
            ],
          }),
          94,
          161000,
        ),
      },
      "2025-12-12T09:22:00.000Z",
      "Dec 12, 2025 · 09:22",
    ),
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9f1b3c",
            projectId: "dev-copilot",
            projectName: "dev-copilot",
            env: "staging",
            applicationType: "AI Coding Assistant",
            connectionMethod: "SDK",
            profile: "Full Security Assessment",
            assessments: [
              "Prompt Injection",
              "Jailbreak",
              "Unsafe Code Generation",
              "Role Escalation",
              "Sensitive Data Leakage",
            ],
          }),
          82,
          192000,
        ),
      },
      "2025-12-12T08:04:00.000Z",
      "Dec 12, 2025 · 08:04",
    ),
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9f0a2d",
            projectId: "support-chat",
            projectName: "support-chat",
            env: "production",
            applicationType: "AI Customer Support Assistant",
            connectionMethod: "REST API",
            profile: "Standard Scan",
          }),
          91,
          118000,
        ),
      },
      "2025-12-11T22:11:00.000Z",
      "Dec 11, 2025 · 22:11",
    ),
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9ef1a8",
            projectId: "ops-agent",
            projectName: "ops-agent",
            env: "production",
            applicationType: "AI Coding Assistant",
            connectionMethod: "Webhook",
            profile: "Full Security Assessment",
            assessments: [
              "Prompt Injection",
              "Jailbreak",
              "Prompt Leakage",
              "Sensitive Data Leakage",
              "Hallucination",
              "Unauthorized Document Retrieval",
              "Role Escalation",
            ],
          }),
          68,
          262000,
        ),
      },
      "2025-12-11T14:39:00.000Z",
      "Dec 11, 2025 · 14:39",
    ),
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9ee0c1",
            projectId: "embed-api",
            projectName: "embed-api",
            env: "development",
            applicationType: "Custom AI Application",
            connectionMethod: "REST API",
            profile: "Quick Scan",
          }),
          88,
          72000,
        ),
      },
      "2025-11-27T11:02:00.000Z",
      "Nov 27, 2025 · 11:02",
    ),
    withCompletedAt(
      {
        ...buildScanResult(
          session({
            id: "rpt_9ed2f4",
            projectId: "voice-realtime",
            projectName: "voice-realtime",
            env: "staging",
            applicationType: "AI Chatbot",
            connectionMethod: "WebSocket",
            profile: "Standard Scan",
          }),
          79,
          146000,
        ),
      },
      "2025-11-26T16:44:00.000Z",
      "Nov 26, 2025 · 16:44",
    ),
  ];
}

export function loadReports(): ScanResultReport[] {
  if (typeof window === "undefined") return seedReports();
  try {
    const raw = localStorage.getItem(REPORTS_KEY);
    if (raw === null) {
      const seeded = seedReports();
      localStorage.setItem(REPORTS_KEY, JSON.stringify(seeded));
      return seeded;
    }
    const parsed = JSON.parse(raw) as ScanResultReport[];
    return Array.isArray(parsed) ? parsed : seedReports();
  } catch {
    return seedReports();
  }
}

export function saveReports(reports: ScanResultReport[]) {
  try {
    localStorage.setItem(REPORTS_KEY, JSON.stringify(reports));
  } catch {
    /* ignore */
  }
}

export function getReportById(id: string): ScanResultReport | null {
  return loadReports().find((r) => r.id === id) ?? null;
}

export function addReport(report: ScanResultReport) {
  const reports = loadReports().filter((r) => r.id !== report.id);
  reports.unshift(report);
  saveReports(reports);
}

export function deleteReport(id: string): ScanResultReport[] {
  const next = loadReports().filter((r) => r.id !== id);
  saveReports(next);
  return next;
}

export function resetReportsToSeed() {
  const seeded = seedReports();
  saveReports(seeded);
  return seeded;
}

export type ReportSort = "date-desc" | "date-asc" | "score-desc" | "score-asc";

export type ReportFilters = {
  search: string;
  env: string;
  risk: string;
  applicationType: string;
  sort: ReportSort;
};

export function filterReports(
  reports: ScanResultReport[],
  filters: ReportFilters,
): ScanResultReport[] {
  const q = filters.search.trim().toLowerCase();
  let next = reports.filter((r) => {
    if (q && !r.projectName.toLowerCase().includes(q) && !r.id.toLowerCase().includes(q)) {
      return false;
    }
    if (filters.env !== "all" && r.env.toLowerCase() !== filters.env.toLowerCase()) return false;
    if (filters.risk !== "all" && r.riskLevel !== filters.risk) return false;
    if (
      filters.applicationType !== "all" &&
      r.applicationType !== filters.applicationType
    ) {
      return false;
    }
    return true;
  });

  next = [...next].sort((a, b) => {
    switch (filters.sort) {
      case "date-asc":
        return new Date(a.completedAt).getTime() - new Date(b.completedAt).getTime();
      case "score-desc":
        return b.score - a.score;
      case "score-asc":
        return a.score - b.score;
      case "date-desc":
      default:
        return new Date(b.completedAt).getTime() - new Date(a.completedAt).getTime();
    }
  });

  return next;
}

export function uniqueEnvs(reports: ScanResultReport[]) {
  return [...new Set(reports.map((r) => r.env))].sort();
}

export function uniqueAppTypes(reports: ScanResultReport[]) {
  return [...new Set(reports.map((r) => r.applicationType))].sort();
}

export function uniqueRisks(reports: ScanResultReport[]) {
  return [...new Set(reports.map((r) => r.riskLevel))];
}
