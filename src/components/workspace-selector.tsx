import { useState } from "react";
import { toast } from "sonner";
import { Check, ChevronDown, Plus, Settings2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PrimaryButton, SecondaryButton, SettingsField, SettingsInput } from "@/components/settings/shared";
import { useWorkspace } from "@/lib/workspace-context";
import { cn } from "@/lib/utils";

export function WorkspaceSelector() {
  const { workspaces, current, setWorkspace, createWorkspace } = useWorkspace();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");

  function switchTo(id: string) {
    if (id === current.id) return;
    const next = setWorkspace(id);
    if (next) {
      toast.success("Workspace switched", {
        description: `Now viewing ${next.name}.`,
      });
    }
  }

  function handleCreate() {
    const created = createWorkspace(name);
    setCreateOpen(false);
    setName("");
    toast.success("Workspace created", {
      description: `${created.name} is ready (mock).`,
    });
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="hidden items-center gap-2 rounded-xl bg-hover/40 px-3 py-1.5 text-left transition-colors hover:bg-hover/70 lg:flex"
            aria-label="Switch workspace"
          >
            <span className="max-w-[140px] truncate font-mono text-[11px] text-muted-foreground">
              {current.slug}
            </span>
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent
          align="start"
          sideOffset={10}
          className="w-[260px] rounded-2xl border-border bg-card/95 p-1.5 shadow-glass backdrop-blur-2xl"
        >
          <div className="px-2.5 py-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              Workspaces
            </div>
          </div>

          {workspaces.map((ws) => {
            const active = ws.id === current.id;
            return (
              <DropdownMenuItem
                key={ws.id}
                className={cn(
                  "cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover",
                  active && "bg-hover/60",
                )}
                onSelect={() => switchTo(ws.id)}
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{ws.name}</div>
                  <div className="truncate font-mono text-[10px] text-muted-foreground">{ws.slug}</div>
                </div>
                {active ? <Check className="h-4 w-4 shrink-0 text-foreground" /> : null}
              </DropdownMenuItem>
            );
          })}

          <DropdownMenuSeparator className="bg-border" />

          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => {
              setName("");
              setCreateOpen(true);
            }}
          >
            <Plus className="h-4 w-4" strokeWidth={1.75} />
            Create Workspace
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => {
              toast.message("Manage Workspaces", {
                description: "Workspace management is a mock placeholder.",
              });
            }}
          >
            <Settings2 className="h-4 w-4" strokeWidth={1.75} />
            Manage Workspaces
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-md gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Workspace
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">
              Create Workspace
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Mock action — the new workspace is stored in local frontend state only.
            </DialogDescription>
          </DialogHeader>
          <div className="p-6">
            <SettingsField label="Workspace Name">
              <SettingsInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Staging Sandbox"
                autoFocus
              />
            </SettingsField>
          </div>
          <DialogFooter className="gap-2 border-t border-border px-6 py-4 sm:space-x-0">
            <SecondaryButton onClick={() => setCreateOpen(false)}>Cancel</SecondaryButton>
            <PrimaryButton onClick={handleCreate} disabled={!name.trim()}>
              Create
            </PrimaryButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
