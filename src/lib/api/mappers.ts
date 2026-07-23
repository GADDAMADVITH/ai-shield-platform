import type { ConnectionMethod, EnvironmentOption } from "@/components/create-project-dialog";
import type { AuthUser } from "@/lib/auth";
import type {
  BackendProject,
  BackendUser,
  ConnectionMethodApi,
  ProjectEnvironment,
} from "@/lib/api/types";
import {
  iconForType,
  inferApplicationType,
  scoreTone,
} from "@/lib/project-display";
import type { Project } from "@/lib/projects";
import { formatDistanceToNow } from "date-fns";

export function roleLabel(role: string): string {
  switch (role) {
    case "admin":
      return "Administrator";
    case "member":
      return "Member";
    case "viewer":
      return "Viewer";
    default:
      return role.charAt(0).toUpperCase() + role.slice(1);
  }
}

export function mapBackendUser(user: BackendUser): AuthUser {
  return {
    id: user.id,
    name: user.full_name,
    email: user.email,
    role: roleLabel(user.role),
  };
}

export function mapEnvironmentToApi(env: EnvironmentOption): ProjectEnvironment {
  return env.toLowerCase() as ProjectEnvironment;
}

export function mapConnectionMethodToApi(method: ConnectionMethod): ConnectionMethodApi {
  switch (method) {
    case "Website Testing (Playwright)":
      return "playwright";
    case "Localhost Service":
      return "localhost";
    case "SDK Integration (Python)":
    case "SDK Integration (Node.js)":
      return "sdk";
    case "REST API":
    default:
      return "rest_api";
  }
}

export function mapConnectionMethodFromApi(
  method: string,
): ConnectionMethod {
  switch (method) {
    case "playwright":
      return "Website Testing (Playwright)";
    case "localhost":
      return "Localhost Service";
    case "sdk":
      return "SDK Integration (Python)";
    case "rest_api":
    default:
      return "REST API";
  }
}

export function mapStatusLabel(status: string): string {
  switch (status) {
    case "connected":
      return "Connected";
    case "disconnected":
      return "Disconnected";
    case "error":
      return "Attention";
    case "archived":
      return "Archived";
    default:
      return status;
  }
}

export function mapBackendProject(project: BackendProject): Project {
  const applicationType = inferApplicationType(project.application_type);
  const score =
    project.status === "connected" ? 90 : project.status === "error" ? 65 : 78;
  return {
    id: project.id,
    name: project.name,
    env: project.environment,
    type: project.application_type,
    applicationType,
    connectionMethod: mapConnectionMethodFromApi(project.connection_method),
    icon: iconForType(applicationType),
    score,
    tone: scoreTone(score),
    status: mapStatusLabel(project.status),
    scans: 0,
    last: formatDistanceToNow(new Date(project.updated_at), { addSuffix: true }),
    runScanDisabled: project.status === "archived" || project.status === "disconnected",
    description: project.description,
    backendStatus: project.status,
  };
}
