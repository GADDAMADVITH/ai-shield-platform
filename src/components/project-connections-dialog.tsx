import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Chip } from "@/components/ui-primitives";
import {
  createConnection,
  deleteConnection,
  listConnections,
  testConnection,
  updateConnection,
} from "@/lib/api/connections";
import { messageForApiError } from "@/lib/api/errors";
import { mapConnectionMethodToApi } from "@/lib/api/mappers";
import type { BackendConnection } from "@/lib/api/types";
import type { ConnectionMethod } from "@/components/create-project-dialog";
import { CONNECTION_METHODS } from "@/components/create-project-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type ProjectConnectionsDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  projectName: string;
};

const fieldClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus-visible:border-foreground/40 focus-visible:bg-surface focus-visible:ring-4 focus-visible:ring-foreground/5";

function statusTone(status: string): "success" | "warning" | "danger" | "muted" {
  if (status === "healthy") return "success";
  if (status === "unhealthy" || status === "error") return "danger";
  if (status === "unverified") return "muted";
  return "warning";
}

export function ProjectConnectionsDialog({
  open,
  onOpenChange,
  projectId,
  projectName,
}: ProjectConnectionsDialogProps) {
  const queryClient = useQueryClient();
  const queryKey = ["connections", projectId] as const;
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("Primary");
  const [method, setMethod] = useState<ConnectionMethod>("REST API");
  const [baseUrl, setBaseUrl] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editUrl, setEditUrl] = useState("");

  const connectionsQuery = useQuery({
    queryKey,
    queryFn: async () => (await listConnections(projectId)).items,
    enabled: open && Boolean(projectId),
  });

  useEffect(() => {
    if (!open) {
      setCreating(false);
      setName("Primary");
      setMethod("REST API");
      setBaseUrl("");
      setEditingId(null);
    }
  }, [open]);

  const invalidate = () => void queryClient.invalidateQueries({ queryKey });

  const createMutation = useMutation({
    mutationFn: async () => {
      const apiMethod = mapConnectionMethodToApi(method);
      return createConnection(projectId, {
        name: name.trim() || "Primary",
        connection_method: apiMethod,
        base_url: apiMethod === "playwright" ? null : baseUrl.trim(),
        health_endpoint: apiMethod === "rest_api" ? "/health" : null,
        playwright_entry_url: apiMethod === "playwright" ? baseUrl.trim() : null,
      });
    },
    onSuccess: () => {
      toast.success("Connection created");
      setCreating(false);
      setBaseUrl("");
      invalidate();
    },
    onError: (error) => toast.error(messageForApiError(error)),
  });

  const testMutation = useMutation({
    mutationFn: (connectionId: string) => testConnection(projectId, connectionId),
    onSuccess: (result) => {
      toast[result.reachable ? "success" : "error"](result.message, {
        description: `Status ${result.status_code ?? "—"} · ${result.response_time_ms}ms`,
      });
      invalidate();
    },
    onError: (error) => toast.error(messageForApiError(error)),
  });

  const deleteMutation = useMutation({
    mutationFn: (connectionId: string) => deleteConnection(projectId, connectionId),
    onSuccess: () => {
      toast.success("Connection deleted");
      invalidate();
    },
    onError: (error) => toast.error(messageForApiError(error)),
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingId) return;
      const conn = connectionsQuery.data?.find((c) => c.id === editingId);
      if (!conn) return;
      const body =
        conn.connection_method === "playwright"
          ? { playwright_entry_url: editUrl.trim() }
          : { base_url: editUrl.trim() };
      return updateConnection(projectId, editingId, body);
    },
    onSuccess: () => {
      toast.success("Connection updated");
      setEditingId(null);
      invalidate();
    },
    onError: (error) => toast.error(messageForApiError(error)),
  });

  function startEdit(connection: BackendConnection) {
    setEditingId(connection.id);
    setEditUrl(connection.playwright_entry_url || connection.base_url || "");
  }

  function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!baseUrl.trim()) {
      toast.error("URL / endpoint is required");
      return;
    }
    createMutation.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[min(90vh,720px)] max-w-lg gap-0 overflow-y-auto rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Connections
          </div>
          <DialogTitle className="text-lg font-semibold tracking-tight">{projectName}</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Manage and test connection configurations for this project.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 px-6 py-5">
          {connectionsQuery.isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading connections…
            </div>
          ) : null}

          {connectionsQuery.data?.length === 0 && !creating ? (
            <p className="text-sm text-muted-foreground">No connections yet.</p>
          ) : null}

          <div className="space-y-3">
            {connectionsQuery.data?.map((connection) => (
              <div
                key={connection.id}
                className="rounded-2xl border border-border bg-surface/40 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-mono text-sm">{connection.name}</div>
                    <div className="mt-0.5 text-[11px] text-muted-foreground">
                      {connection.connection_method}
                    </div>
                  </div>
                  <Chip tone={statusTone(connection.status)}>{connection.status}</Chip>
                </div>
                <div className="mt-3 grid gap-1 font-mono text-[11px] text-muted-foreground">
                  <div>
                    Reachable:{" "}
                    {connection.status === "healthy"
                      ? "yes"
                      : connection.status === "unhealthy"
                        ? "no"
                        : "untested"}
                  </div>
                  <div>
                    Last verified:{" "}
                    {connection.last_verified_at
                      ? new Date(connection.last_verified_at).toLocaleString()
                      : "Never"}
                  </div>
                  <div className="truncate">
                    URL: {connection.playwright_entry_url || connection.base_url || "—"}
                  </div>
                </div>

                {editingId === connection.id ? (
                  <form
                    className="mt-3 space-y-2"
                    onSubmit={(e) => {
                      e.preventDefault();
                      updateMutation.mutate();
                    }}
                  >
                    <Input
                      value={editUrl}
                      onChange={(e) => setEditUrl(e.target.value)}
                      className={fieldClass}
                      placeholder="https://…"
                    />
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="rounded-xl bg-foreground px-3 py-1.5 text-xs font-medium text-background"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="rounded-xl border border-border px-3 py-1.5 text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => testMutation.mutate(connection.id)}
                      disabled={testMutation.isPending}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface/50 px-3 py-1.5 text-xs hover:bg-hover"
                    >
                      <Activity className="h-3.5 w-3.5" />
                      Test
                    </button>
                    <button
                      type="button"
                      onClick={() => startEdit(connection)}
                      className="rounded-xl border border-border bg-surface/50 px-3 py-1.5 text-xs hover:bg-hover"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteMutation.mutate(connection.id)}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface/50 px-3 py-1.5 text-xs text-destructive hover:bg-hover"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {creating ? (
            <form className="space-y-3 rounded-2xl border border-border p-4" onSubmit={handleCreate}>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Connection name"
                className={fieldClass}
              />
              <Select value={method} onValueChange={(v) => setMethod(v as ConnectionMethod)}>
                <SelectTrigger className={fieldClass}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONNECTION_METHODS.map((opt) => (
                    <SelectItem key={opt} value={opt}>
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.example.com"
                className={fieldClass}
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="rounded-xl bg-foreground px-3 py-2 text-xs font-medium text-background"
                >
                  {createMutation.isPending ? "Saving…" : "Save connection"}
                </button>
                <button
                  type="button"
                  onClick={() => setCreating(false)}
                  className="rounded-xl border border-border px-3 py-2 text-xs"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              type="button"
              onClick={() => setCreating(true)}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm hover:bg-hover"
            >
              <Plus className="h-4 w-4" /> Add connection
            </button>
          )}
        </div>

        <DialogFooter className="border-t border-border px-6 py-4">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-xl border border-border px-3 py-2 text-sm"
          >
            Close
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
