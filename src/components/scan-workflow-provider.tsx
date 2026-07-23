import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { CheckCircle2 } from "lucide-react";
import { CreateProjectDialog, type CreateProjectPayload } from "@/components/create-project-dialog";
import { StartScanDialog } from "@/components/start-scan-dialog";
import { Toaster } from "@/components/ui/sonner";
import { ProjectsProvider, useProjects } from "@/lib/projects";
import { useTheme } from "@/lib/theme";
import { pushNotification } from "@/lib/notifications-store";

type ScanWorkflowContextValue = {
  openStartScan: (projectId?: string) => void;
  openCreateProject: () => void;
};

const ScanWorkflowContext = createContext<ScanWorkflowContextValue | null>(null);

export function useScanWorkflow() {
  const ctx = useContext(ScanWorkflowContext);
  if (!ctx) throw new Error("useScanWorkflow must be used within ScanWorkflowProvider");
  return ctx;
}

function ScanWorkflowInner({ children }: { children: ReactNode }) {
  const { theme } = useTheme();
  const { addProject } = useProjects();
  const [scanOpen, setScanOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [preselectedProjectId, setPreselectedProjectId] = useState<string | null>(null);
  const [reopenScanAfterCreate, setReopenScanAfterCreate] = useState(false);

  const openStartScan = useCallback((projectId?: string) => {
    setPreselectedProjectId(projectId ?? null);
    setScanOpen(true);
  }, []);

  const openCreateProject = useCallback(() => {
    setReopenScanAfterCreate(false);
    setCreateOpen(true);
  }, []);

  async function handleCreate(payload: CreateProjectPayload) {
    const project = await addProject(payload);
    toast.success("Project created", {
      description: `${project.name} is registered and connected.`,
      icon: <CheckCircle2 className="h-4 w-4 text-success" />,
    });
    pushNotification({
      title: "Project Created",
      description: `New AI application “${project.name}” added successfully.`,
      category: "projects",
      severity: "success",
    });
    if (reopenScanAfterCreate) {
      setPreselectedProjectId(project.id);
      setScanOpen(true);
    }
    setReopenScanAfterCreate(false);
  }

  function handleRequestCreateFromScan() {
    setReopenScanAfterCreate(true);
    setScanOpen(false);
    setCreateOpen(true);
  }

  return (
    <ScanWorkflowContext.Provider value={{ openStartScan, openCreateProject }}>
      {children}
      <Toaster position="top-right" theme={theme} richColors closeButton />
      <StartScanDialog
        open={scanOpen}
        onOpenChange={setScanOpen}
        onRequestCreateProject={handleRequestCreateFromScan}
        preselectedProjectId={preselectedProjectId}
      />
      <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} onCreate={handleCreate} />
    </ScanWorkflowContext.Provider>
  );
}

export function ScanWorkflowProvider({ children }: { children: ReactNode }) {
  return (
    <ProjectsProvider>
      <ScanWorkflowInner>{children}</ScanWorkflowInner>
    </ProjectsProvider>
  );
}
