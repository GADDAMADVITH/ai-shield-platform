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
  clearAllNotifications,
  deleteNotification,
  filterNotifications,
  loadNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATIONS_EVENT,
  pushNotification,
  unreadCount,
  type AppNotification,
  type NotificationFilter,
  type PushNotificationInput,
} from "@/lib/notifications-store";

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

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [hydrated, setHydrated] = useState(false);

  const sync = useCallback(() => {
    setNotifications(loadNotifications());
  }, []);

  useEffect(() => {
    sync();
    setHydrated(true);
    const onChange = () => sync();
    window.addEventListener(NOTIFICATIONS_EVENT, onChange);
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener(NOTIFICATIONS_EVENT, onChange);
      window.removeEventListener("storage", onChange);
    };
  }, [sync]);

  const notify = useCallback((input: PushNotificationInput) => {
    return pushNotification(input);
  }, []);

  const markRead = useCallback((id: string) => {
    setNotifications(markNotificationRead(id));
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications(markAllNotificationsRead());
  }, []);

  const remove = useCallback((id: string) => {
    setNotifications(deleteNotification(id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications(clearAllNotifications());
  }, []);

  const refresh = useCallback(() => {
    sync();
  }, [sync]);

  const value = useMemo<NotificationsContextValue>(
    () => ({
      notifications: hydrated ? notifications : [],
      unread: unreadCount(hydrated ? notifications : []),
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
