export type Workspace = {
  id: string;
  name: string;
  /** Compact label shown in the navbar */
  slug: string;
};

const STORAGE_KEY = "ais-workspace-id";
const LIST_KEY = "ais-workspaces";

export const DEFAULT_WORKSPACES: Workspace[] = [
  { id: "ws_prod", name: "AIShield Production", slug: "aishield-prod" },
  { id: "ws_dev", name: "AIShield Development", slug: "aishield-dev" },
  { id: "ws_research", name: "Research Workspace", slug: "research-ws" },
  { id: "ws_demo", name: "Demo Workspace", slug: "demo-ws" },
];

export const DEFAULT_WORKSPACE_ID = "ws_prod";

export function loadWorkspaces(): Workspace[] {
  if (typeof window === "undefined") return DEFAULT_WORKSPACES;
  try {
    const raw = localStorage.getItem(LIST_KEY);
    if (!raw) {
      localStorage.setItem(LIST_KEY, JSON.stringify(DEFAULT_WORKSPACES));
      return DEFAULT_WORKSPACES;
    }
    const parsed = JSON.parse(raw) as Workspace[];
    if (!Array.isArray(parsed) || parsed.length === 0) return DEFAULT_WORKSPACES;
    return parsed;
  } catch {
    return DEFAULT_WORKSPACES;
  }
}

export function saveWorkspaces(workspaces: Workspace[]) {
  try {
    localStorage.setItem(LIST_KEY, JSON.stringify(workspaces));
  } catch {
    /* ignore */
  }
}

export function loadSelectedWorkspaceId(): string {
  if (typeof window === "undefined") return DEFAULT_WORKSPACE_ID;
  try {
    const id = localStorage.getItem(STORAGE_KEY);
    if (!id) return DEFAULT_WORKSPACE_ID;
    const workspaces = loadWorkspaces();
    return workspaces.some((w) => w.id === id) ? id : DEFAULT_WORKSPACE_ID;
  } catch {
    return DEFAULT_WORKSPACE_ID;
  }
}

export function saveSelectedWorkspaceId(id: string) {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

export function slugifyWorkspaceName(name: string) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 24) || "workspace";
}
