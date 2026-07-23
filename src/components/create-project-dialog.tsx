import { useState, type FormEvent, type ReactNode } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export const APPLICATION_TYPES = [
  "AI Chatbot",
  "RAG / Document Q&A",
  "AI Coding Assistant",
  "AI Customer Support Assistant",
  "Healthcare Assistant",
  "Finance Assistant",
  "Education Assistant",
  "Legal Assistant",
  "Resume Analyzer",
  "Translation Assistant",
  "Email Assistant",
  "Marketing Assistant",
  "Meeting Summarizer",
  "Business Analytics Assistant",
  "Custom AI Application",
] as const;

export const CONNECTION_METHODS = [
  "REST API",
  "Website Testing (Playwright)",
  "Localhost Service",
  "SDK Integration (Python)",
  "SDK Integration (Node.js)",
] as const;

export const ENVIRONMENTS = ["Development", "Staging", "Production"] as const;

export type ApplicationType = (typeof APPLICATION_TYPES)[number];
export type ConnectionMethod = (typeof CONNECTION_METHODS)[number];
export type EnvironmentOption = (typeof ENVIRONMENTS)[number];

export type CreateProjectPayload = {
  name: string;
  applicationType: ApplicationType;
  connectionMethod: ConnectionMethod;
  environment: EnvironmentOption;
  targetUrl: string;
  description: string;
};

const fieldClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus-visible:border-foreground/40 focus-visible:bg-surface focus-visible:ring-4 focus-visible:ring-foreground/5";

const selectTriggerClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus:ring-4 focus:ring-foreground/5 data-[placeholder]:text-muted-foreground";

const selectContentClass =
  "z-[60] rounded-2xl border-border bg-popover/95 backdrop-blur-2xl";

type CreateProjectDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (payload: CreateProjectPayload) => void;
};

export function CreateProjectDialog({ open, onOpenChange, onCreate }: CreateProjectDialogProps) {
  const [name, setName] = useState("");
  const [applicationType, setApplicationType] = useState<ApplicationType | "">("");
  const [connectionMethod, setConnectionMethod] = useState<ConnectionMethod | "">("");
  const [environment, setEnvironment] = useState<EnvironmentOption | "">("");
  const [targetUrl, setTargetUrl] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function reset() {
    setName("");
    setApplicationType("");
    setConnectionMethod("");
    setEnvironment("");
    setTargetUrl("");
    setDescription("");
    setErrors({});
  }

  function handleOpenChange(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = "Project name is required";
    if (!applicationType) next.applicationType = "Application type is required";
    if (!connectionMethod) next.connectionMethod = "Connection method is required";
    if (!environment) next.environment = "Environment is required";
    if (!targetUrl.trim()) next.targetUrl = "Target URL / endpoint is required";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    onCreate({
      name: name.trim(),
      applicationType: applicationType as ApplicationType,
      connectionMethod: connectionMethod as ConnectionMethod,
      environment: environment as EnvironmentOption,
      targetUrl: targetUrl.trim(),
      description: description.trim(),
    });
    handleOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[min(90vh,720px)] max-w-lg gap-0 overflow-y-auto rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Projects
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">
              Create New Project
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Register an AI application to begin security assessments.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 px-6 py-5">
            <Field label="Project Name" required error={errors.name}>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Customer Support AI"
                className={fieldClass}
              />
            </Field>

            <Field label="Application Type" required error={errors.applicationType}>
              <Select
                value={applicationType || undefined}
                onValueChange={(v) => setApplicationType(v as ApplicationType)}
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
            </Field>

            <Field label="Connection Method" required error={errors.connectionMethod}>
              <Select
                value={connectionMethod || undefined}
                onValueChange={(v) => setConnectionMethod(v as ConnectionMethod)}
              >
                <SelectTrigger className={selectTriggerClass}>
                  <SelectValue placeholder="Select connection method" />
                </SelectTrigger>
                <SelectContent className={selectContentClass}>
                  {CONNECTION_METHODS.map((opt) => (
                    <SelectItem key={opt} value={opt} className="rounded-xl">
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Environment" required error={errors.environment}>
              <Select
                value={environment || undefined}
                onValueChange={(v) => setEnvironment(v as EnvironmentOption)}
              >
                <SelectTrigger className={selectTriggerClass}>
                  <SelectValue placeholder="Select environment" />
                </SelectTrigger>
                <SelectContent className={selectContentClass}>
                  {ENVIRONMENTS.map((opt) => (
                    <SelectItem key={opt} value={opt} className="rounded-xl">
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Target URL / Endpoint" required error={errors.targetUrl}>
              <Input
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://api.example.com/chat"
                className={fieldClass}
              />
            </Field>

            <Field label="Description">
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional notes about this AI application…"
                rows={3}
                className={cn(fieldClass, "min-h-[84px] resize-none")}
              />
            </Field>
          </div>

          <DialogFooter className="gap-2 border-t border-border px-6 py-4 sm:space-x-0">
            <button
              type="button"
              onClick={() => handleOpenChange(false)}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
            >
              Create Project
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
        {required ? " *" : ""}
      </span>
      {children}
      {error ? <span className="mt-1.5 block text-xs text-destructive">{error}</span> : null}
    </label>
  );
}
