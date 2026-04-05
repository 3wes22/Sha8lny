import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

vi.mock("@/lib/api", () => ({
  notificationApi: {
    getStats: vi.fn().mockResolvedValue({
      total_count: 2,
      unread_count: 1,
      urgent_count: 0,
      by_type: {},
      recent_notifications: [],
    }),
    list: vi.fn().mockResolvedValue({
      results: [
        {
          id: "notification-1",
          title: "Roadmap updated",
          message: "A new milestone is ready.",
          notification_type: "roadmap",
          created_at: "2026-04-04T12:00:00Z",
        },
      ],
    }),
    markAllRead: vi.fn(),
  },
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
}));

import NotificationsPage from "@/features/notifications/routes/NotificationsPage";
import { render } from "@/test/utils";

describe("NotificationsPage", () => {
  it("renders notifications", async () => {
    render(<NotificationsPage />);

    expect(await screen.findByText(/Roadmap updated/i)).toBeInTheDocument();
  });
});
