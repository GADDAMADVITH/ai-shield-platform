import { apiRequest } from "@/lib/api/client";
import type {
  BackendProject,
  ProjectEnvironment,
  ProjectListResponse,
  ProjectStatus,
} from "@/lib/api/types";

export type CreateProjectBody = {
  name: string;
  environment: ProjectEnvironment;
  application_type: string;
  connection_method: string;
  description?: string | null;
};

export type UpdateProjectBody = {
  name?: string;
  description?: string | null;
  environment?: ProjectEnvironment;
  application_type?: string;
  connection_method?: string;
  status?: ProjectStatus;
};

export async function listProjects(page = 1, pageSize = 100): Promise<ProjectListResponse> {
  return apiRequest<ProjectListResponse>(`/projects?page=${page}&page_size=${pageSize}`);
}

export async function getProject(projectId: string): Promise<BackendProject> {
  return apiRequest<BackendProject>(`/projects/${projectId}`);
}

export async function createProject(body: CreateProjectBody): Promise<BackendProject> {
  return apiRequest<BackendProject>("/projects", { method: "POST", body });
}

export async function updateProject(
  projectId: string,
  body: UpdateProjectBody,
): Promise<BackendProject> {
  return apiRequest<BackendProject>(`/projects/${projectId}`, { method: "PATCH", body });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiRequest(`/projects/${projectId}`, { method: "DELETE" });
}

export async function archiveProject(projectId: string): Promise<BackendProject> {
  return updateProject(projectId, { status: "archived" });
}
