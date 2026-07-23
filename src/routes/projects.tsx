import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Plus, Filter, MoreHorizontal, ArrowUpRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { Card, Chip, ScoreRing, StatusDot } from "@/components/ui-primitives";
import { ProjectConnectionsDialog } from "@/components/project-connections-dialog";
import { useProjects, type Project } from "@/lib/projects";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import { requireAuth } from "@/lib/auth";
import { messageForApiError } from "@/lib/api/errors";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const Route = createFileRoute("/projects")({
  beforeLoad: () => {
    requireAuth();
  },
  head: () => ({
    meta: [
      { title: "Projects · AI Shield" },
      { name: "description", content: "All AI projects continuously monitored by AI Shield." },
      { property: "og:title", content: "Projects · AI Shield" },
      { property: "og:description", content: "All AI projects continuously monitored by AI Shield." },
    ],
  }),
  component: Projects,
});

function Projects() {
  const { projects, isLoading, isError, error, refetch, archiveProject, deleteProject } =
    useProjects();
  const { openCreateProject, openStartScan } = useScanWorkflow();
  const [connectionsProject, setConnectionsProject] = useState<Project | null>(null);

  async function handleArchive(project: Project) {
    try {
      await archiveProject(project.id);
      toast.success("Project archived", { description: project.name });
    } catch (err) {
      toast.error(messageForApiError(err));
    }
  }

  async function handleDelete(project: Project) {
    try {
      await deleteProject(project.id);
      toast.success("Project deleted", { description: project.name });
    } catch (err) {
      toast.error(messageForApiError(err));
    }
  }

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Fleet</div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">Continuous observability across every AI surface.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Filter className="h-4 w-4" /> Filter
          </button>
          <button
            type="button"
            onClick={() => openCreateProject()}
            className="inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background hover:scale-[1.02] transition-transform"
          >
            <Plus className="h-4 w-4" strokeWidth={2.25} /> New project
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 py-16 justify-center text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading projects…
        </div>
      ) : null}

      {isError ? (
        <Card className="!p-5">
          <p className="text-sm text-destructive">{messageForApiError(error)}</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-xl border border-border px-3 py-2 text-sm"
          >
            Retry
          </button>
        </Card>
      ) : null}

      {!isLoading && !isError && projects.length === 0 ? (
        <Card className="!p-8 text-center">
          <p className="text-sm text-muted-foreground">No projects yet. Create your first AI application.</p>
          <button
            type="button"
            onClick={() => openCreateProject()}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background"
          >
            <Plus className="h-4 w-4" /> New project
          </button>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {projects.map((p, i) => {
          const Icon = p.icon;
          return (
            <Card key={p.id} className="animate-float-in !p-5" style={{ animationDelay: `${i * 50}ms` }}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="grid h-11 w-11 place-items-center rounded-2xl border border-border bg-elevated">
                    <Icon className="h-5 w-5 text-foreground" strokeWidth={1.6} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 font-mono text-sm">{p.name}</div>
                    <div className="mt-0.5 text-[11px] text-muted-foreground">{p.type}</div>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button type="button" className="text-muted-foreground hover:text-foreground">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="rounded-2xl">
                    <DropdownMenuItem onClick={() => setConnectionsProject(p)}>
                      Connections
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => void handleArchive(p)}>
                      Archive
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => void handleDelete(p)}
                    >
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="my-5 flex items-center justify-center py-2">
                <ScoreRing score={p.score} size={132} strokeWidth={8} label={p.env} />
              </div>

              <div className="mb-3 flex items-center justify-between text-xs">
                <div className="inline-flex items-center gap-1.5 text-muted-foreground">
                  <StatusDot tone={p.tone} /> {p.status}
                </div>
                <Chip tone={p.tone}>{p.env}</Chip>
              </div>

              <div className="grid grid-cols-2 gap-2 border-t border-border pt-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Scans</div>
                  <div className="font-mono text-sm">{p.scans}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Last</div>
                  <div className="font-mono text-sm">{p.last}</div>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  disabled={p.runScanDisabled}
                  onClick={() => openStartScan(p.id)}
                  className="flex-1 rounded-xl bg-foreground py-2 text-xs font-medium text-background transition-transform hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100"
                >
                  Run scan
                </button>
                <button
                  type="button"
                  onClick={() => setConnectionsProject(p)}
                  className="inline-flex items-center gap-1 rounded-xl border border-border bg-surface/50 px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
                >
                  Open <ArrowUpRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </Card>
          );
        })}
      </div>

      {connectionsProject ? (
        <ProjectConnectionsDialog
          open={Boolean(connectionsProject)}
          onOpenChange={(open) => {
            if (!open) setConnectionsProject(null);
          }}
          projectId={connectionsProject.id}
          projectName={connectionsProject.name}
        />
      ) : null}
    </AppShell>
  );
}
