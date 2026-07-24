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
  filterNotifications,
  pushNotification,
  type AppNotification,
  type NotificationFilter,
  type NotificationSeverity,
  type PushNotificationInput,
} from "@/lib/notifications-store";
import {
  deleteNotification as apiDeleteNotification,
  listNotifications,
  markAllNotificationsRead as apiMarkAllRead,
  markNotificationRead as apiMarkRead,
} from "@/lib/api/notifications";
import type { BackendNotification, SeverityApi } from "@/lib/api/types";
import { getAccessToken } from "@/lib/api/client";

type NotificationsContextValue = {
  notifications: AppNotification[];
  unread: number;
  filter: NotificationFilter;
  setFilter: (filter: NotificationFilter) => void;
  filtered: AppNotification[];
  notify: (input: PushNotificationInput) => AppNotification;
  markRead: (id: string) => void;
  markAllRead: () => void;
  remove: (id: string) => void;
  clearAll: () => void;
  refresh: () => void;
};

const NotificationsContext = createContext<NotificationsContextValue | null>(null);

function mapSeverity(severity: SeverityApi, level: BackendNotification["level"]): NotificationSeverity {
  if (level === "critical" || severity === "critical") return "danger";
  if (level === "warning" || severity === "high" || severity === "medium") return "warning";
  if (severity === "info" || severity === "low") return "info";
  return "info";
}

function mapBackendNotification(n: BackendNotification): AppNotification {
  return {
    id: n.id,
    title: n.title,
    description: n.description,
    category: n.category,
    severity: mapSeverity(n.severity, n.level),
    createdAt: n.created_at,
    read: n.is_read,
  };
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [hydrated, setHydrated] = useState(false);

  const sync = useCallback(async () => {
    if (!getAccessToken()) {
      setNotifications([]);
      setHydrated(true);
      return;
    }
    try {
      const page = await listNotifications({ page: 1, pageSize: 50 });
      setNotifications(page.items.map(mapBackendNotification));
    } catch {
      // Keep existing list on transient failures.
    } finally {
      setHydrated(true);
    }
  }, []);

  useEffect(() => {
    void sync();
    const id = window.setInterval(() => {
      void sync();
    }, 60_000);
    return () => window.clearInterval(id);
  }, [sync]);

  const notify = useCallback((input: PushNotificationInput) => {
    // Optimistic local push for in-session UX (scan workflow); backend emits durable events.
    return pushNotification(input);
  }, []);

  const markRead = useCallback((id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    void apiMarkRead(id, true).catch(() => undefined);
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    void apiMarkAllRead().catch(() => undefined);
  }, []);

  const remove = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    void apiDeleteNotification(id).catch(() => undefined);
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const refresh = useCallback(() => {
    void sync();
  }, [sync]);

  const value = useMemo<NotificationsContextValue>(
    () => ({
      notifications: hydrated ? notifications : [],
      unread: (hydrated ? notifications : []).filter((n) => !n.read).length,
      filter,
      setFilter,
      filtered: filterNotifications(hydrated ? notifications : [], filter),
      notify,
      markRead,
      markAllRead,
      remove,
      clearAll,
      refresh,
    }),
    [
      hydrated,
      notifications,
      filter,
      notify,
      markRead,
      markAllRead,
      remove,
      clearAll,
      refresh,
    ],
  );

  return (
    <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
