import { useState } from "react";
import { toast } from "sonner";
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  RefreshCw,
  ShieldAlert,
  FileText,
  FolderKanban,
  Settings2,
  AlertTriangle,
  Info,
  CheckCircle2,
  X,
} from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Chip } from "@/components/ui-primitives";
import { useNotifications } from "@/lib/notifications-context";
import {
  formatBadgeCount,
  pushNotification,
  relativeTime,
  type AppNotification,
  type NotificationFilter,
  type NotificationSeverity,
} from "@/lib/notifications-store";
import { cn } from "@/lib/utils";

const FILTERS: { id: NotificationFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "unread", label: "Unread" },
  { id: "security", label: "Security" },
  { id: "system", label: "System" },
  { id: "reports", label: "Reports" },
  { id: "projects", label: "Projects" },
];

function severityTone(severity: NotificationSeverity): "success" | "warning" | "danger" | "info" | "muted" {
  if (severity === "success") return "success";
  if (severity === "warning") return "warning";
  if (severity === "danger") return "danger";
  if (severity === "info") return "info";
  return "muted";
}

function NotificationIcon({ n }: { n: AppNotification }) {
  const className = "h-4 w-4";
  if (n.category === "security") {
    if (n.severity === "danger" || n.severity === "warning") {
      return <ShieldAlert className={cn(className, "text-destructive")} strokeWidth={1.75} />;
    }
    return <CheckCircle2 className={cn(className, "text-success")} strokeWidth={1.75} />;
  }
  if (n.category === "reports") {
    return <FileText className={cn(className, "text-info")} strokeWidth={1.75} />;
  }
  if (n.category === "projects") {
    return <FolderKanban className={cn(className, "text-foreground")} strokeWidth={1.75} />;
  }
  if (n.severity === "warning") {
    return <AlertTriangle className={cn(className, "text-warning")} strokeWidth={1.75} />;
  }
  if (n.severity === "info") {
    return <Info className={cn(className, "text-info")} strokeWidth={1.75} />;
  }
  return <Settings2 className={cn(className, "text-muted-foreground")} strokeWidth={1.75} />;
}

export function NotificationCenter() {
  const {
    filtered,
    unread,
    filter,
    setFilter,
    markRead,
    markAllRead,
    remove,
    clearAll,
    refresh,
    notifications,
  } = useNotifications();
  const [open, setOpen] = useState(false);
  const badge = formatBadgeCount(unread);

  function handleRefresh() {
    refresh();
    if (notifications.length === 0) {
      pushNotification({
        title: "Workspace synced",
        description: "Notification feed refreshed. No new security events.",
        category: "system",
        severity: "info",
      });
    }
    toast.success("Notifications refreshed", { description: "Mock sync complete." });
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label="Notifications"
          className="relative grid h-9 w-9 place-items-center rounded-xl bg-hover/40 text-muted-foreground transition-colors hover:text-foreground"
        >
          <Bell className="h-4 w-4" />
          {badge ? (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-info px-1 font-mono text-[9px] font-medium leading-none text-white">
              {badge}
            </span>
          ) : null}
        </button>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={10}
        className="w-[min(100vw-2rem,420px)] overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl"
      >
        <div className="flex items-start justify-between gap-3 border-b border-border px-4 py-3.5">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Inbox
            </div>
            <div className="mt-0.5 text-sm font-semibold tracking-tight">Notifications</div>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              title="Mark all as read"
              disabled={unread === 0}
              onClick={() => {
                markAllRead();
                toast.success("All notifications marked as read");
              }}
              className="grid h-8 w-8 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-hover hover:text-foreground disabled:opacity-40"
            >
              <CheckCheck className="h-4 w-4" />
            </button>
            <button
              type="button"
              title="Clear all"
              disabled={notifications.length === 0}
              onClick={() => {
                clearAll();
                toast.success("All notifications cleared");
              }}
              className="grid h-8 w-8 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-hover hover:text-destructive disabled:opacity-40"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex gap-1 overflow-x-auto border-b border-border px-3 py-2">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={cn(
                "shrink-0 rounded-lg px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] transition-colors",
                filter === f.id
                  ? "bg-hover text-foreground"
                  : "text-muted-foreground hover:bg-hover/60 hover:text-foreground",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="max-h-[min(60vh,420px)] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-2xl border border-border bg-elevated">
                <Bell className="h-5 w-5 text-muted-foreground" strokeWidth={1.6} />
              </div>
              <p className="mt-4 text-sm font-medium">No notifications.</p>
              <p className="mt-1 text-[12px] text-muted-foreground">
                You&apos;re all caught up for now.
              </p>
              <button
                type="button"
                onClick={handleRefresh}
                className="mt-5 inline-flex items-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </button>
            </div>
          ) : (
            <ul>
              {filtered.map((n) => (
                <li
                  key={n.id}
                  className={cn(
                    "group border-b border-border/60 px-4 py-3 transition-colors last:border-b-0 hover:bg-hover/40",
                    !n.read && "bg-hover/20",
                  )}
                >
                  <div className="flex gap-3">
                    <div className="relative mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-border bg-elevated/60">
                      <NotificationIcon n={n} />
                      {!n.read ? (
                        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-info" />
                      ) : null}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium">{n.title}</div>
                          <p className="mt-0.5 text-[12.5px] leading-relaxed text-muted-foreground">
                            {n.description}
                          </p>
                        </div>
                        <button
                          type="button"
                          title="Dismiss"
                          onClick={() => remove(n.id)}
                          className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-muted-foreground opacity-0 transition-opacity hover:bg-hover hover:text-foreground group-hover:opacity-100"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>

                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <Chip tone={severityTone(n.severity)}>{n.severity}</Chip>
                        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                          {n.category}
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {relativeTime(n.createdAt)}
                        </span>
                        {!n.read ? (
                          <button
                            type="button"
                            onClick={() => markRead(n.id)}
                            className="ml-auto inline-flex items-center gap-1 rounded-lg px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground transition-colors hover:bg-hover hover:text-foreground"
                          >
                            <Check className="h-3 w-3" /> Mark read
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
