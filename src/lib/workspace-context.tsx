import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DEFAULT_WORKSPACE_ID,
  loadSelectedWorkspaceId,
  loadWorkspaces,
  saveSelectedWorkspaceId,
  saveWorkspaces,
  slugifyWorkspaceName,
  type Workspace,
} from "@/lib/workspace-store";

type WorkspaceContextValue = {
  workspaces: Workspace[];
  current: Workspace;
  setWorkspace: (id: string) => Workspace | null;
  createWorkspace: (name: string) => Workspace;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentId, setCurrentId] = useState(DEFAULT_WORKSPACE_ID);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const list = loadWorkspaces();
    setWorkspaces(list);
    setCurrentId(loadSelectedWorkspaceId());
    setHydrated(true);
  }, []);

  const current = useMemo(() => {
    const list = hydrated ? workspaces : loadWorkspaces();
    return list.find((w) => w.id === currentId) ?? list[0]!;
  }, [hydrated, workspaces, currentId]);

  const setWorkspace = useCallback(
    (id: string) => {
      const next = workspaces.find((w) => w.id === id);
      if (!next) return null;
      setCurrentId(id);
      saveSelectedWorkspaceId(id);
      return next;
    },
    [workspaces],
  );

  const createWorkspace = useCallback((name: string) => {
    const trimmed = name.trim() || "New Workspace";
    const created: Workspace = {
      id: `ws_${Date.now().toString(36)}`,
      name: trimmed,
      slug: slugifyWorkspaceName(trimmed),
    };
    setWorkspaces((prev) => {
      const next = [...prev, created];
      saveWorkspaces(next);
      return next;
    });
    setCurrentId(created.id);
    saveSelectedWorkspaceId(created.id);
    return created;
  }, []);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      workspaces: hydrated ? workspaces : [],
      current,
      setWorkspace,
      createWorkspace,
    }),
    [hydrated, workspaces, current, setWorkspace, createWorkspace],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}
