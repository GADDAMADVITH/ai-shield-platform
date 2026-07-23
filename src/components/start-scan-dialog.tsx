import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { CheckCircle2, Loader2, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  APPLICATION_TYPES,
  type ApplicationType,
} from "@/components/create-project-dialog";
import {
  ASSESSMENT_PROFILES,
  BASE_ASSESSMENTS,
  architectureAssessments,
  saveScanSession,
  useProjects,
  type AssessmentProfile,
  type Project,
} from "@/lib/projects";
import { pushNotification } from "@/lib/notifications-store";
import { cn } from "@/lib/utils";

const selectTriggerClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus:ring-4 focus:ring-foreground/5 data-[placeholder]:text-muted-foreground";

const selectContentClass =
  "z-[60] rounded-2xl border-border bg-popover/95 backdrop-blur-2xl";

const readOnlyClass =
  "w-full rounded-xl border border-border bg-elevated/40 px-3 py-2.5 text-sm text-muted-foreground";

type StartScanDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRequestCreateProject: () => void;
  preselectedProjectId?: string | null;
};

export function StartScanDialog({
  open,
  onOpenChange,
  onRequestCreateProject,
  preselectedProjectId,
}: StartScanDialogProps) {
  const { projects } = useProjects();
  const navigate = useNavigate();

  const [projectId, setProjectId] = useState("");
  const [applicationType, setApplicationType] = useState<ApplicationType | "">("");
  const [profile, setProfile] = useState<AssessmentProfile | "">("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const project = useMemo(
    () => projects.find((p) => p.id === projectId) ?? null,
    [projects, projectId],
  );

  const archAssessments = useMemo(
    () => architectureAssessments(applicationType || project?.applicationType || ""),
    [applicationType, project],
  );

  const allAssessments = useMemo(
    () => [...BASE_ASSESSMENTS, ...archAssessments],
    [archAssessments],
  );

  useEffect(() => {
    if (!open) return;
    const initial =
      (preselectedProjectId && projects.find((p) => p.id === preselectedProjectId)) ||
      projects[0] ||
      null;
    if (initial) {
      applyProject(initial);
    } else {
      setProjectId("");
      setApplicationType("");
      setProfile("");
      setSelected({});
    }
    setErrors({});
    setSubmitting(false);
  }, [open, preselectedProjectId, projects]);

  useEffect(() => {
    setSelected((prev) => {
      const next: Record<string, boolean> = {};
      for (const name of allAssessments) {
        next[name] = prev[name] ?? true;
      }
      return next;
    });
  }, [allAssessments]);

  function applyProject(p: Project) {
    setProjectId(p.id);
    setApplicationType(p.applicationType);
    setProfile("Standard Scan");
  }

  function resetAndClose() {
    onOpenChange(false);
  }

  function toggleAssessment(name: string) {
    setSelected((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  function validate() {
    const next: Record<string, string> = {};
    if (!projects.length) next.project = "Create a project to start a scan";
    else if (!projectId) next.project = "Select a project";
    if (!applicationType) next.applicationType = "Application type is required";
    if (!profile) next.profile = "Assessment profile is required";
    const enabled = allAssessments.filter((a) => selected[a]);
    if (!enabled.length) next.assessments = "Select at least one assessment";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate() || !project || !profile || !applicationType) return;

    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 700));

    const assessments = allAssessments.filter((a) => selected[a]);
    saveScanSession({
      id: `scn_${Date.now().toString(36)}`,
      projectId: project.id,
      projectName: project.name,
      env: project.env,
      applicationType,
      connectionMethod: project.connectionMethod,
      profile,
      assessments,
      startedAt: Date.now(),
    });

    toast.success("Security assessment started.", {
      description: `${project.name} · ${profile}`,
      icon: <CheckCircle2 className="h-4 w-4 text-success" />,
    });
    pushNotification({
      title: "Scan Started",
      description: `Security assessment started for ${project.name} (${profile}).`,
      category: "security",
      severity: "info",
    });

    setSubmitting(false);
    onOpenChange(false);
    void navigate({ to: "/scan" });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[min(90vh,760px)] max-w-lg gap-0 overflow-y-auto rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Assessment
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">
              Start Security Assessment
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Configure a security assessment for your AI application.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-5 px-6 py-5">
            {/* Project */}
            <section>
              <FieldLabel>Project *</FieldLabel>
              {projects.length === 0 ? (
                <div className="rounded-2xl border border-border bg-surface/40 p-4">
                  <p className="text-sm text-muted-foreground">No projects available</p>
                  <button
                    type="button"
                    onClick={onRequestCreateProject}
                    className="mt-3 inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
                  >
                    <Plus className="h-4 w-4" strokeWidth={2.25} />
                    Create Project
                  </button>
                </div>
              ) : (
                <Select
                  value={projectId || undefined}
                  onValueChange={(id) => {
                    const p = projects.find((x) => x.id === id);
                    if (p) applyProject(p);
                  }}
                >
                  <SelectTrigger className={selectTriggerClass}>
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent className={selectContentClass}>
                    {projects.map((p) => (
                      <SelectItem key={p.id} value={p.id} className="rounded-xl">
                        <span className="font-mono">{p.name}</span>
                        <span className="text-muted-foreground"> · {p.env}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              {errors.project ? <ErrorText>{errors.project}</ErrorText> : null}
            </section>

            {/* Application Type */}
            <section>
              <FieldLabel>Application Type *</FieldLabel>
              <Select
                value={applicationType || undefined}
                onValueChange={(v) => setApplicationType(v as ApplicationType)}
                disabled={!project}
              >
                <SelectTrigger className={selectTriggerClass}>
                  <SelectValue placeholder="Select application type" />
                </SelectTrigger>
                <SelectContent className={selectContentClass}>
                  {APPLICATION_TYPES.map((opt) => (
                    <SelectItem key={opt} value={opt} className="rounded-xl">
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.applicationType ? <ErrorText>{errors.applicationType}</ErrorText> : null}
            </section>

            {/* Connection Method */}
            <section>
              <FieldLabel>Connection Method *</FieldLabel>
              <div className={readOnlyClass}>
                {project?.connectionMethod ?? "—"}
              </div>
            </section>

            {/* Profile */}
            <section>
              <FieldLabel>Assessment Profile *</FieldLabel>
              <Select
                value={profile || undefined}
                onValueChange={(v) => setProfile(v as AssessmentProfile)}
              >
                <SelectTrigger className={selectTriggerClass}>
                  <SelectValue placeholder="Select assessment profile" />
                </SelectTrigger>
                <SelectContent className={selectContentClass}>
                  {ASSESSMENT_PROFILES.map((opt) => (
                    <SelectItem key={opt.id} value={opt.id} className="rounded-xl">
                      <span className="flex w-full items-center justify-between gap-4">
                        <span>{opt.id}</span>
                        <span className="font-mono text-[11px] text-muted-foreground">{opt.duration}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.profile ? <ErrorText>{errors.profile}</ErrorText> : null}
            </section>

            {/* Assessments */}
            <section>
              <FieldLabel>Assessments *</FieldLabel>
              <div className="space-y-2 rounded-2xl border border-border bg-surface/40 p-3">
                {BASE_ASSESSMENTS.map((name) => (
                  <AssessmentRow
                    key={name}
                    name={name}
                    checked={!!selected[name]}
                    onToggle={() => toggleAssessment(name)}
                  />
                ))}
                {archAssessments.length > 0 ? (
                  <>
                    <div className="my-2 border-t border-border pt-2 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                      Architecture-specific
                    </div>
                    {archAssessments.map((name) => (
                      <AssessmentRow
                        key={name}
                        name={name}
                        checked={!!selected[name]}
                        onToggle={() => toggleAssessment(name)}
                      />
                    ))}
                  </>
                ) : null}
              </div>
              {errors.assessments ? <ErrorText>{errors.assessments}</ErrorText> : null}
            </section>
          </div>

          <DialogFooter className="gap-2 border-t border-border px-6 py-4 sm:space-x-0">
            <button
              type="button"
              onClick={resetAndClose}
              disabled={submitting}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || projects.length === 0}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {submitting ? "Starting…" : "Start Scan"}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <div className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
      {children}
    </div>
  );
}

function ErrorText({ children }: { children: ReactNode }) {
  return <p className="mt-1.5 text-xs text-destructive">{children}</p>;
}

function AssessmentRow({
  name,
  checked,
  onToggle,
}: {
  name: string;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <label
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-xl px-2 py-2 transition-colors hover:bg-hover/50",
      )}
    >
      <Checkbox checked={checked} onCheckedChange={onToggle} className="rounded-md border-border" />
      <span className="text-sm">{name}</span>
    </label>
  );
}
