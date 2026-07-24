import type { ActiveScanSession } from "@/lib/projects";

export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";
export type FindingStatus = "Open" | "Accepted Risk" | "Mitigated" | "Informational";

export type SecurityFinding = {
  id: string;
  title: string;
  severity: FindingSeverity;
  category: string;
  description: string;
  impact: string;
  recommendation: string;
  status: FindingStatus;
};

export type ScoreBreakdownItem = {
  label: string;
  score: number;
};

export type ScanResultReport = {
  id: string;
  /** Backend scan UUID when the report is backed by the API. */
  scanId?: string;
  projectName: string;
  env: string;
  applicationType: string;
  connectionMethod: string;
  profile: string;
  score: number;
  grade: string;
  riskLevel: "Low" | "Moderate" | "Elevated" | "High";
  scanTime: string;
  completedAt: string;
  elapsedLabel: string;
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    passed: number;
    totalTests: number;
  };
  findings: SecurityFinding[];
  breakdown: ScoreBreakdownItem[];
  recommendations: { priority: "P0" | "P1" | "P2"; text: string }[];
};

const RESULT_KEY = "ais-scan-result";

export function gradeForScore(score: number) {
  if (score >= 90) return "A";
  if (score >= 85) return "A-";
  if (score >= 80) return "B+";
  if (score >= 70) return "B";
  if (score >= 60) return "C";
  return "D";
}

export function riskForScore(score: number): ScanResultReport["riskLevel"] {
  if (score >= 90) return "Low";
  if (score >= 80) return "Moderate";
  if (score >= 70) return "Elevated";
  return "High";
}

function formatScanTime(ms: number) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const s = (total % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

const FINDING_CATALOG: Omit<SecurityFinding, "id" | "status">[] = [
  {
    title: "Prompt Injection",
    severity: "high",
    category: "Prompt Security",
    description:
      "Crafted inputs successfully overrode system instructions and redirected model behavior outside the intended policy boundary.",
    impact: "Attackers could coerce the model into disclosing internal instructions or executing unauthorized actions.",
    recommendation: "Strengthen prompt isolation, add input validation, and enforce output policy filters on untrusted content.",
  },
  {
    title: "Jailbreak Vulnerability",
    severity: "medium",
    category: "Model Safety",
    description:
      "Multi-turn jailbreak vectors partially bypassed safety rails under adversarial role-play framing.",
    impact: "Elevated risk of policy evasion and generation of disallowed content under sustained probing.",
    recommendation: "Expand jailbreak regression suites and tighten refusal heuristics for multi-step adversarial dialogues.",
  },
  {
    title: "Prompt Leakage",
    severity: "high",
    category: "Privacy",
    description:
      "The model echoed fragments of the system prompt when asked to summarize hidden instructions.",
    impact: "System prompts and proprietary policy text may be recoverable by end users.",
    recommendation: "Redact system-prompt content from outputs and apply canary-token monitoring for leakage.",
  },
  {
    title: "Sensitive Data Exposure",
    severity: "critical",
    category: "Data Security",
    description:
      "Responses included PII-like tokens reconstructed from retrieved context without sufficient redaction.",
    impact: "Potential leakage of customer or employee personal data through model responses.",
    recommendation: "Enable output filtering and sanitize retrieved documents before grounding.",
  },
  {
    title: "Hallucination Risk",
    severity: "medium",
    category: "Output Validation",
    description:
      "The model asserted unsupported facts with high confidence when context was sparse or conflicting.",
    impact: "Users may act on fabricated guidance, increasing operational and compliance risk.",
    recommendation: "Require citation grounding and confidence thresholds before emitting factual claims.",
  },
  {
    title: "Unauthorized Retrieval",
    severity: "high",
    category: "Authorization",
    description:
      "Retrieval probes accessed documents outside the authenticated tenant scope in mock authorization tests.",
    impact: "Cross-tenant or privileged document exposure via RAG tooling.",
    recommendation: "Enforce document ACLs at retrieval time and audit vector-store query filters.",
  },
  {
    title: "Unsafe Code Generation",
    severity: "medium",
    category: "Model Safety",
    description:
      "Coding assistant suggestions included shell patterns that could escalate privileges if executed naively.",
    impact: "Developers may introduce insecure scripts into production workflows.",
    recommendation: "Block dangerous shell patterns and require safe-by-default coding templates.",
  },
  {
    title: "Role Escalation",
    severity: "low",
    category: "Authorization",
    description:
      "Conversation manipulation briefly convinced the assistant to adopt an elevated operator persona.",
    impact: "Minor privilege confusion that could unlock restricted tool calls if combined with other flaws.",
    recommendation: "Bind tool permissions to verified identity claims rather than conversational role labels.",
  },
];

function pickFindings(assessments: string[], score: number): SecurityFinding[] {
  const wanted = new Set(
    assessments.map((a) => a.toLowerCase()).concat(
      // always include a representative set for the report
      ["prompt injection", "jailbreak", "prompt leakage", "sensitive", "hallucination"],
    ),
  );

  const matched = FINDING_CATALOG.filter((f) => {
    const t = f.title.toLowerCase();
    for (const w of wanted) {
      if (t.includes(w) || w.includes(t.split(" ")[0]!)) return true;
      if (w.includes("retrieval") && t.includes("retrieval")) return true;
      if (w.includes("unsafe") && t.includes("unsafe")) return true;
      if (w.includes("role") && t.includes("role")) return true;
      if ((w.includes("sensitive") || w.includes("pii") || w.includes("data leakage")) && t.includes("sensitive"))
        return true;
    }
    return false;
  });

  const base = (matched.length ? matched : FINDING_CATALOG).slice(0, score >= 90 ? 4 : score >= 80 ? 6 : 8);

  return base.map((f, i) => ({
    ...f,
    id: `fnd_${i + 1}`,
    status: (f.severity === "critical" || f.severity === "high"
      ? "Open"
      : f.severity === "low"
        ? "Accepted Risk"
        : "Open") as FindingStatus,
  }));
}

export function buildScanResult(
  session: ActiveScanSession,
  score: number,
  elapsedMs: number,
): ScanResultReport {
  const findings = pickFindings(session.assessments, score);
  const critical = findings.filter((f) => f.severity === "critical").length;
  const high = findings.filter((f) => f.severity === "high").length;
  const medium = findings.filter((f) => f.severity === "medium").length;
  const low = findings.filter((f) => f.severity === "low").length;
  const totalTests = Math.max(session.assessments.length * 4, findings.length + 12);
  const passed = Math.max(0, totalTests - findings.length);

  const now = new Date();
  return {
    id: session.id,
    scanId: session.id,
    projectName: session.projectName,
    env: session.env,
    applicationType: session.applicationType,
    connectionMethod: String(session.connectionMethod),
    profile: session.profile,
    score,
    grade: gradeForScore(score),
    riskLevel: riskForScore(score),
    scanTime: now.toLocaleString(),
    completedAt: now.toISOString(),
    elapsedLabel: formatScanTime(elapsedMs),
    summary: { critical, high, medium, low, passed, totalTests },
    findings,
    breakdown: [
      { label: "Prompt Security", score: clamp(score - 4 + (critical ? -6 : 2)) },
      { label: "Data Security", score: clamp(score - (critical ? 12 : 2)) },
      { label: "Model Safety", score: clamp(score - (medium ? 5 : 0)) },
      { label: "Output Validation", score: clamp(score - 3) },
      { label: "Authorization", score: clamp(score - (high ? 8 : 1)) },
      { label: "Privacy", score: clamp(score - (critical || high ? 7 : 2)) },
    ],
    recommendations: [
      { priority: "P0", text: "Enable output filtering." },
      { priority: "P0", text: "Sanitize retrieved documents." },
      { priority: "P1", text: "Strengthen system prompts." },
      { priority: "P1", text: "Implement rate limiting." },
      { priority: "P1", text: "Add input validation." },
      { priority: "P2", text: "Improve prompt isolation." },
    ],
  };
}

function clamp(n: number) {
  return Math.max(35, Math.min(99, Math.round(n)));
}

export function saveScanResult(result: ScanResultReport) {
  try {
    sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
  } catch {
    /* ignore */
  }
}

export function loadScanResult(): ScanResultReport | null {
  try {
    const raw = sessionStorage.getItem(RESULT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ScanResultReport;
  } catch {
    return null;
  }
}

/** Demo fallback when visiting /results without a completed scan */
export function demoScanResult(): ScanResultReport {
  return buildScanResult(
    {
      id: "scn_demo",
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
      startedAt: Date.now() - 185000,
    },
    86,
    185000,
  );
}
