import { apiRequest } from "@/lib/api/client";
import type { BackendNotification, NotificationListResponse } from "@/lib/api/types";

export async function listNotifications(params?: {
  page?: number;
  pageSize?: number;
  unreadOnly?: boolean;
  category?: string;
}): Promise<NotificationListResponse> {
  const search = new URLSearchParams({
    page: String(params?.page ?? 1),
    page_size: String(params?.pageSize ?? 50),
  });
  if (params?.unreadOnly) search.set("unread_only", "true");
  if (params?.category) search.set("category", params.category);
  return apiRequest<NotificationListResponse>(`/notifications?${search.toString()}`);
}

export async function markNotificationRead(
  notificationId: string,
  isRead = true,
): Promise<BackendNotification> {
  return apiRequest<BackendNotification>(`/notifications/${notificationId}`, {
    method: "PATCH",
    body: { is_read: isRead },
  });
}

export async function markAllNotificationsRead(): Promise<{ message: string }> {
  return apiRequest("/notifications/mark-all-read", { method: "POST" });
}

export async function deleteNotification(notificationId: string): Promise<{ message: string }> {
  return apiRequest(`/notifications/${notificationId}`, { method: "DELETE" });
}
