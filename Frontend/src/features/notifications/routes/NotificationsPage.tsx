import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { notificationApi, type NotificationListItem, type NotificationStats, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { toast } from "sonner";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationListItem[]>([]);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const [statsResponse, notificationsResponse] = await Promise.all([
          notificationApi.getStats(),
          notificationApi.list(),
        ]);

        setStats(statsResponse);
        setNotifications(notificationsResponse.results);
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to load notifications"));
      } finally {
        setLoading(false);
      }
    };

    void loadNotifications();
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllRead();
      const refreshedStats = await notificationApi.getStats();
      setStats(refreshedStats);
      setNotifications((previous) => previous.map((notification) => ({ ...notification, is_read: true })));
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update notifications"));
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <PageShell
      actions={<Button onClick={handleMarkAllRead} variant="outline">Mark all read</Button>}
      description="Notification state should stay legible from the shell and on this dedicated surface."
      eyebrow="Notifications"
      title="Activity feed"
    >
      {stats ? (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="panel-paper rounded-[1.5rem] p-5">
            <p className="type-kicker">Total</p>
            <p className="mt-3 text-3xl font-bold">{stats.total_count}</p>
          </div>
          <div className="panel-paper rounded-[1.5rem] p-5">
            <p className="type-kicker">Unread</p>
            <p className="mt-3 text-3xl font-bold">{stats.unread_count}</p>
          </div>
          <div className="panel-paper rounded-[1.5rem] p-5">
            <p className="type-kicker">Urgent</p>
            <p className="mt-3 text-3xl font-bold">{stats.urgent_count}</p>
          </div>
        </div>
      ) : null}

      {notifications.length > 0 ? (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div className="atlas-panel p-5" key={notification.id}>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xl font-bold">{notification.title}</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{notification.message}</p>
                </div>
                <div className="text-right text-sm text-muted-foreground">
                  <p>{notification.display_type ?? notification.notification_type}</p>
                  <p>{notification.time_ago ?? new Date(notification.created_at).toLocaleString()}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <StatePanel
          description="New learning, roadmap, and job events will appear here."
          state="empty"
          title="No notifications yet"
        />
      )}
    </PageShell>
  );
}
