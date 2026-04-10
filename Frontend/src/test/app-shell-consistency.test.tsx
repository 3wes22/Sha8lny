import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      full_name: "Shell User",
      username: "shelluser",
      email: "shell@example.com",
    },
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: ReactNode }) => children,
}));

vi.mock("@/lib/api", () => ({
  notificationApi: {
    getStats: vi.fn().mockResolvedValue({
      unread_count: 2,
      recent_notifications: [{ title: "Roadmap updated", created_at: "2026-04-04T12:00:00Z" }],
    }),
  },
}));

import { ROUTES, PRIMARY_NAV_ITEMS } from "@/app/routes";
import { MainLayout } from "@/shared/layout/MainLayout";
import { render } from "@/test/utils";

describe("app shell consistency", () => {
  it("shows every primary nav item and the atlas shell context", async () => {
    render(<MainLayout><div>shell content</div></MainLayout>, { route: ROUTES.dashboard });

    const navigation = screen.getByRole("navigation", { name: /primary navigation/i });

    expect(await screen.findByText("Roadmap updated")).toBeInTheDocument();
    expect(screen.getByText("Sha8alny")).toBeInTheDocument();
    expect(screen.getByText("Surface 01")).toBeInTheDocument();
    expect(screen.getByText("shell content")).toBeInTheDocument();
    PRIMARY_NAV_ITEMS.forEach((item) => {
      expect(within(navigation).getByText(item.title)).toBeInTheDocument();
    });
  });

  it("renders the mobile atlas menu outside the clipped header shell", async () => {
    render(<MainLayout><div>shell content</div></MainLayout>, { route: ROUTES.dashboard });
    await screen.findByText("Roadmap updated");

    fireEvent.click(screen.getByRole("button", { name: /open atlas navigation/i }));

    const headerShell = screen.getByTestId("atlas-header-shell");
    const menuLayer = screen.getByTestId("mobile-atlas-menu-layer");
    const menuPanel = screen.getByTestId("mobile-atlas-menu-panel");
    const mobileNavigation = within(menuPanel).getByRole("navigation", {
      name: /primary navigation/i,
    });

    expect(mobileNavigation).toBeInTheDocument();
    expect(within(headerShell).queryByTestId("mobile-atlas-menu-panel")).not.toBeInTheDocument();
    expect(menuLayer).toContainElement(menuPanel);
    expect(menuPanel.className).toMatch(/overflow-y-auto/);
    expect(menuPanel.className).toMatch(/max-h-/);
  });
});
