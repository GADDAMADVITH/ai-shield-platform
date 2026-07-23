import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Bot, Braces, MessageSquare, Workflow } from "lucide-react";
import {
  APPLICATION_TYPES,
  type ApplicationType,
  type ConnectionMethod,
  type CreateProjectPayload,
  type EnvironmentOption,
} from "@/components/create-project-dialog";

export type ProjectTone = "success" | "warning" | "danger" | "info" | "muted";

export type Project = {
  id: string;
  name: string;
  env: string;
  type: string;
  applicationType: ApplicationType;
  connectionMethod: ConnectionMethod;
  icon: LucideIcon;
  score: number;
  tone: ProjectTone;
  status: string;
  scans: number;
  last: string;
  runScanDisabled?: boolean;
};

export function scoreTone(score: number): ProjectTone {
  if (score >= 90) return "success";
  if (score >= 80) return "warning";
  return "danger";
}

export function iconForType(type: ApplicationType | string): LucideIcon {
  if (type.includes("RAG") || type.includes("Document")) return Bot;
  if (type.includes("Coding") || type.includes("Agent") || type.includes("Autonomous")) return Workflow;
  if (type.includes("Custom") || type.includes("Analytics") || type.includes("Resume") || type.includes("Embeddings"))
    return Braces;
  return MessageSquare;
}

export function inferApplicationType(type: string): ApplicationType {
  const normalized = type.toLowerCase();
  if (normalized.includes("rag") || normalized.includes("document")) return "RAG / Document Q&A";
  if (normalized.includes("coding") || normalized.includes("copilot") || normalized.includes("agent"))
    return "AI Coding Assistant";
  if (normalized.includes("support") || normalized.includes("customer"))
    return "AI Customer Support Assistant";
  if (normalized.includes("chat") || normalized.includes("voice")) return "AI Chatbot";
  if (normalized.includes("embed")) return "Custom AI Application";
  const match = APPLICATION_TYPES.find((t) => t === type);
  return match ?? "Custom AI Application";
}

export function buildProjectFromPayload(payload: CreateProjectPayload): Project {
  const score = 70 + Math.floor(Math.random() * 31);
  return {
    id: `proj_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    name: payload.name,
    env: payload.environment.toLowerCase(),
    type: payload.applicationType,
    applicationType: payload.applicationType,
    connectionMethod: payload.connectionMethod,
    icon: iconForType(payload.applicationType),
    score,
    tone: scoreTone(score),
    status: "Connected",
    scans: 0,
    last: "Never",
    runScanDisabled: true,
  };
}

const INITIAL_PROJECTS: Project[] = [
  {
    id: "knowledge-rag",
    name: "knowledge-rag",
    env: "production",
    type: "RAG · GPT-4o",
    applicationType: "RAG / Document Q&A",
    connectionMethod: "REST API",
    icon: Bot,
    score: 96,
    tone: "success",
    status: "Connected",
    scans: 128,
    last: "12 min ago",
  },
  {
    id: "dev-copilot",
    name: "dev-copilot",
    env: "staging",
    type: "Agent · Claude 3.5",
    applicationType: "AI Coding Assistant",
    connectionMethod: "SDK Integration (Node.js)",
    icon: Workflow,
    score: 82,
    tone: "warning",
    status: "Connected",
    scans: 74,
    last: "1h ago",
  },
  {
    id: "support-chat",
    name: "support-chat",
    env: "production",
    type: "Chat · Llama 3",
    applicationType: "AI Customer Support Assistant",
    connectionMethod: "REST API",
    icon: MessageSquare,
    score: 91,
    tone: "success",
    status: "Connected",
    scans: 212,
    last: "26 min ago",
  },
  {
    id: "ops-agent",
    name: "ops-agent",
    env: "production",
    type: "Autonomous · Multi-tool",
    applicationType: "AI Coding Assistant",
    connectionMethod: "SDK Integration (Python)",
    icon: Workflow,
    score: 68,
    tone: "danger",
    status: "Attention",
    scans: 41,
    last: "3h ago",
  },
  {
    id: "embed-api",
    name: "embed-api",
    env: "development",
    type: "Embeddings API",
    applicationType: "Custom AI Application",
    connectionMethod: "REST API",
    icon: Braces,
    score: 88,
    tone: "success",
    status: "Connected",
    scans: 55,
    last: "2h ago",
  },
  {
    id: "voice-realtime",
    name: "voice-realtime",
    env: "staging",
    type: "Realtime · Voice",
    applicationType: "AI Chatbot",
    connectionMethod: "Website Testing (Playwright)",
    icon: MessageSquare,
    score: 79,
    tone: "warning",
    status: "Syncing",
    scans: 22,
    last: "8m ago",
  },
];

type ProjectsContextValue = {
  projects: Project[];
  addProject: (payload: CreateProjectPayload) => Project;
};

const ProjectsContext = createContext<ProjectsContextValue | null>(null);

export function ProjectsProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);

  const value = useMemo<ProjectsContextValue>(
    () => ({
      projects,
      addProject: (payload) => {
        const project = buildProjectFromPayload(payload);
        setProjects((prev) => [project, ...prev]);
        return project;
      },
    }),
    [projects],
  );

  return <ProjectsContext.Provider value={value}>{children}</ProjectsContext.Provider>;
}

export function useProjects() {
  const ctx = useContext(ProjectsContext);
  if (!ctx) throw new Error("useProjects must be used within ProjectsProvider");
  return ctx;
}

export type AssessmentProfile = "Quick Scan" | "Standard Scan" | "Full Security Assessment";

export const ASSESSMENT_PROFILES: { id: AssessmentProfile; duration: string }[] = [
  { id: "Quick Scan", duration: "~2 min" },
  { id: "Standard Scan", duration: "~8 min" },
  { id: "Full Security Assessment", duration: "~25 min" },
];

export const BASE_ASSESSMENTS = [
  "Prompt Injection",
  "Jailbreak",
  "Prompt Leakage",
  "Sensitive Data Leakage",
  "Hallucination",
] as const;

export function architectureAssessments(applicationType: string): string[] {
  const t = applicationType.toLowerCase();
  if (t.includes("rag") || t.includes("document")) {
    return ["Retrieval Manipulation", "Context Leakage", "Unauthorized Document Retrieval"];
  }
  if (t.includes("coding")) {
    return ["Unsafe Code Generation", "SQL Injection Generation", "Dangerous Shell Commands"];
  }
  if (t.includes("customer support") || t.includes("support assistant")) {
    return ["Customer Data Leakage", "Internal Prompt Exposure"];
  }
  if (t.includes("chatbot") || t.includes("chat")) {
    return ["Role Escalation", "Conversation Manipulation", "System Prompt Exposure"];
  }
  return [];
}

export type ScanAssessmentStatus = "queued" | "running" | "done";

export type ScanAssessment = {
  name: string;
  status: ScanAssessmentStatus;
  severity: "success" | "warning" | "danger" | "info" | "muted";
  time: string;
  findings: number;
};

export type ScanLogLine = { t: string; l: string };

export type ActiveScanSession = {
  id: string;
  projectId: string;
  projectName: string;
  env: string;
  applicationType: string;
  connectionMethod: ConnectionMethod | string;
  profile: AssessmentProfile;
  assessments: string[];
  startedAt: number;
};

const SCAN_SESSION_KEY = "ais-active-scan";

export function saveScanSession(session: ActiveScanSession) {
  try {
    sessionStorage.setItem(SCAN_SESSION_KEY, JSON.stringify(session));
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("ais-scan-started", { detail: session }));
  }
}

export function loadScanSession(): ActiveScanSession | null {
  try {
    const raw = sessionStorage.getItem(SCAN_SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ActiveScanSession;
  } catch {
    return null;
  }
}

export function clearScanSession() {
  try {
    sessionStorage.removeItem(SCAN_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export type { EnvironmentOption };
