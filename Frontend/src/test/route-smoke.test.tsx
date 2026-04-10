import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";

vi.mock("@/features/auth/context/AuthContext", () => ({
  ProtectedRoute: ({ children }: { children: ReactNode }) => children,
  AuthProvider: ({ children }: { children: ReactNode }) => children,
  useAuth: () => ({
    user: null,
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

const stubPage = (label: string) => () => <div>{label}</div>;

vi.mock("@/features/marketing/routes/LandingPage", () => ({ default: stubPage("landing-route") }));
vi.mock("@/features/auth/routes/LoginPage", () => ({ default: stubPage("login-route") }));
vi.mock("@/features/auth/routes/RegisterPage", () => ({ default: stubPage("register-route") }));
vi.mock("@/features/auth/routes/ForgotPasswordPage", () => ({ default: stubPage("forgot-password-route") }));
vi.mock("@/features/dashboard/routes/DashboardPage", () => ({ default: stubPage("dashboard-route") }));
vi.mock("@/features/assessment/routes/AssessmentPage", () => ({ default: stubPage("assessment-route") }));
vi.mock("@/features/assessment/routes/AssessmentSessionPage", () => ({ default: stubPage("assessment-session-route") }));
vi.mock("@/features/assessment/routes/AssessmentResultsPage", () => ({ default: stubPage("assessment-results-route") }));
vi.mock("@/features/roadmap/routes/RoadmapPage", () => ({ default: stubPage("roadmap-route") }));
vi.mock("@/features/advisory/routes/AdvisoryPage", () => ({ default: stubPage("advisor-route") }));
vi.mock("@/features/jobs/routes/JobsPage", () => ({ default: stubPage("jobs-route") }));
vi.mock("@/features/jobs/routes/SavedJobsPage", () => ({ default: stubPage("saved-jobs-route") }));
vi.mock("@/features/jobs/routes/JobDetailPage", () => ({ default: stubPage("job-detail-route") }));
vi.mock("@/features/notifications/routes/NotificationsPage", () => ({ default: stubPage("notifications-route") }));
vi.mock("@/features/profile/routes/ProfilePage", () => ({ default: stubPage("profile-route") }));
vi.mock("@/features/settings/routes/SettingsPage", () => ({ default: stubPage("settings-route") }));
vi.mock("@/shared/layout/MainLayout", () => ({
  MainLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { AppRoutes } from "@/app/AppRoutes";
import { APP_ROUTE_PATTERNS, ROUTES } from "@/app/routes";

describe("route smoke", () => {
  it("keeps route patterns unique", () => {
    expect(new Set(APP_ROUTE_PATTERNS).size).toBe(APP_ROUTE_PATTERNS.length);
  });

  it("renders public routes", async () => {
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={[ROUTES.login]}
      >
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByText("login-route")).toBeInTheDocument();
  });

  it("renders protected routes", async () => {
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={[ROUTES.dashboard]}
      >
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByText("dashboard-route")).toBeInTheDocument();
  });

  it("renders dynamic job detail routes", async () => {
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={[ROUTES.jobDetail("job-1")]}
      >
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByText("job-detail-route")).toBeInTheDocument();
  });
});
