import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import type { LucideIcon } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type ApplicationType,
  type ConnectionMethod,
  type CreateProjectPayload,
  type EnvironmentOption,
} from "@/components/create-project-dialog";
import { createConnection } from "@/lib/api/connections";
import {
  mapConnectionMethodToApi,
  mapBackendProject,
  mapEnvironmentToApi,
} from "@/lib/api/mappers";
import {
  archiveProject as archiveProjectApi,
  createProject as createProjectApi,
  deleteProject as deleteProjectApi,
  listProjects,
  updateProject as updateProjectApi,
} from "@/lib/api/projects";
import type { ProjectStatus } from "@/lib/api/types";
import { useAuth } from "@/lib/auth-context";
import {
  iconForType,
  inferApplicationType,
  scoreTone,
  type ProjectTone,
} from "@/lib/project-display";

export type { ProjectTone };
export { iconForType, inferApplicationType, scoreTone };

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
  description?: string | null;
  backendStatus?: ProjectStatus;
};

export const PROJECTS_QUERY_KEY = ["projects"] as const;

type ProjectsContextValue = {
  projects: Project[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
  addProject: (payload: CreateProjectPayload) => Promise<Project>;
  updateProject: (
    projectId: string,
    patch: {
      name?: string;
      description?: string | null;
      status?: ProjectStatus;
    },
  ) => Promise<Project>;
  archiveProject: (projectId: string) => Promise<Project>;
  deleteProject: (projectId: string) => Promise<void>;
};

const ProjectsContext = createContext<ProjectsContextValue | null>(null);

export function ProjectsProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const projectsQuery = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: async () => {
      const page = await listProjects(1, 100);
      return page.items.map(mapBackendProject);
    },
    enabled: isAuthenticated,
  });

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
  }, [queryClient]);

  const createMutation = useMutation({
    mutationFn: async (payload: CreateProjectPayload) => {
      const created = await createProjectApi({
        name: payload.name,
        environment: mapEnvironmentToApi(payload.environment),
        application_type: payload.applicationType,
        connection_method: payload.connectionMethod,
        description: payload.description || null,
      });

      const method = mapConnectionMethodToApi(payload.connectionMethod);
      await createConnection(created.id, {
        name: "Primary",
        connection_method: method,
        base_url: method === "playwright" ? null : payload.targetUrl,
        health_endpoint: method === "rest_api" ? "/health" : null,
        playwright_entry_url: method === "playwright" ? payload.targetUrl : null,
        notes: "Created with project",
      });

      return mapBackendProject(created);
    },
    onSuccess: () => invalidate(),
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      projectId,
      patch,
    }: {
      projectId: string;
      patch: { name?: string; description?: string | null; status?: ProjectStatus };
    }) => mapBackendProject(await updateProjectApi(projectId, patch)),
    onSuccess: () => invalidate(),
  });

  const archiveMutation = useMutation({
    mutationFn: async (projectId: string) => mapBackendProject(await archiveProjectApi(projectId)),
    onSuccess: () => invalidate(),
  });

  const deleteMutation = useMutation({
    mutationFn: async (projectId: string) => deleteProjectApi(projectId),
    onSuccess: () => invalidate(),
  });

  const value = useMemo<ProjectsContextValue>(
    () => ({
      projects: projectsQuery.data ?? [],
      isLoading: projectsQuery.isLoading,
      isError: projectsQuery.isError,
      error: projectsQuery.error instanceof Error ? projectsQuery.error : null,
      refetch: () => {
        void projectsQuery.refetch();
      },
      addProject: (payload) => createMutation.mutateAsync(payload),
      updateProject: (projectId, patch) =>
        updateMutation.mutateAsync({ projectId, patch }),
      archiveProject: (projectId) => archiveMutation.mutateAsync(projectId),
      deleteProject: (projectId) => deleteMutation.mutateAsync(projectId),
    }),
    [
      projectsQuery.data,
      projectsQuery.isLoading,
      projectsQuery.isError,
      projectsQuery.error,
      projectsQuery,
      createMutation,
      updateMutation,
      archiveMutation,
      deleteMutation,
    ],
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
