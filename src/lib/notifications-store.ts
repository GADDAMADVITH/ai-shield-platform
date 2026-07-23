export type NotificationCategory = "security" | "system" | "reports" | "projects";

export type NotificationSeverity = "success" | "warning" | "info" | "danger";

export type AppNotification = {
  id: string;
  title: string;
  description: string;
  category: NotificationCategory;
  severity: NotificationSeverity;
  createdAt: string;
  read: boolean;
};

export type NotificationFilter = "all" | "unread" | "security" | "system" | "reports" | "projects";

export type PushNotificationInput = {
  title: string;
  description: string;
  category: NotificationCategory;
  severity?: NotificationSeverity;
};

const STORAGE_KEY = "ais-notifications";
export const NOTIFICATIONS_EVENT = "ais-notifications-changed";

function emitChange() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(NOTIFICATIONS_EVENT));
  }
}

function minutesAgo(mins: number) {
  return new Date(Date.now() - mins * 60_000).toISOString();
}

export function seedNotifications(): AppNotification[] {
  return [
    {
      id: "ntf_seed_1",
      title: "Scan Completed",
      description: "Security assessment completed for Customer Support AI.",
      category: "security",
      severity: "success",
      createdAt: minutesAgo(12),
      read: false,
    },
    {
      id: "ntf_seed_2",
      title: "High Risk Detected",
      description: "Critical Prompt Injection vulnerability detected.",
      category: "security",
      severity: "danger",
      createdAt: minutesAgo(45),
      read: false,
    },
    {
      id: "ntf_seed_3",
      title: "Report Generated",
      description: "Security report exported successfully.",
      category: "reports",
      severity: "info",
      createdAt: minutesAgo(90),
      read: false,
    },
    {
      id: "ntf_seed_4",
      title: "Project Created",
      description: "New AI application added successfully.",
      category: "projects",
      severity: "success",
      createdAt: minutesAgo(180),
      read: true,
    },
    {
      id: "ntf_seed_5",
      title: "API Connection Lost",
      description: "Unable to reach REST endpoint.",
      category: "system",
      severity: "warning",
      createdAt: minutesAgo(360),
      read: true,
    },
    {
      id: "ntf_seed_6",
      title: "Settings Updated",
      description: "Profile settings updated successfully.",
      category: "system",
      severity: "success",
      createdAt: minutesAgo(720),
      read: true,
    },
  ];
}

export function loadNotifications(): AppNotification[] {
  if (typeof window === "undefined") return seedNotifications();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) {
      const seeded = seedNotifications();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(seeded));
      return seeded;
    }
    const parsed = JSON.parse(raw) as AppNotification[];
    return Array.isArray(parsed) ? parsed : seedNotifications();
  } catch {
    return seedNotifications();
  }
}

export function saveNotifications(items: AppNotification[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    /* ignore */
  }
  emitChange();
}

export function unreadCount(items: AppNotification[]) {
  return items.filter((n) => !n.read).length;
}

export function formatBadgeCount(count: number) {
  if (count <= 0) return null;
  if (count > 99) return "99+";
  return String(count);
}

export function filterNotifications(items: AppNotification[], filter: NotificationFilter) {
  switch (filter) {
    case "unread":
      return items.filter((n) => !n.read);
    case "security":
    case "system":
    case "reports":
    case "projects":
      return items.filter((n) => n.category === filter);
    case "all":
    default:
      return items;
  }
}

export function pushNotification(input: PushNotificationInput): AppNotification {
  const next: AppNotification = {
    id: `ntf_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    title: input.title,
    description: input.description,
    category: input.category,
    severity: input.severity ?? "info",
    createdAt: new Date().toISOString(),
    read: false,
  };
  const items = [next, ...loadNotifications()];
  saveNotifications(items.slice(0, 100));
  return next;
}

export function markNotificationRead(id: string) {
  const items = loadNotifications().map((n) => (n.id === id ? { ...n, read: true } : n));
  saveNotifications(items);
  return items;
}

export function markAllNotificationsRead() {
  const items = loadNotifications().map((n) => ({ ...n, read: true }));
  saveNotifications(items);
  return items;
}

export function deleteNotification(id: string) {
  const items = loadNotifications().filter((n) => n.id !== id);
  saveNotifications(items);
  return items;
}

export function clearAllNotifications() {
  saveNotifications([]);
  return [] as AppNotification[];
}

export function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}
