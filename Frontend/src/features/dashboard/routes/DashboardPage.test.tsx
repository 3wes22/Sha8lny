import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: () => ({
    user: { full_name: "Mona Ali", username: "mona" },
  }),
}));

vi.mock("@/lib/api", () => ({
  roadmapApi: {
    list: vi
      .fn()
      .mockResolvedValueOnce({ results: [{ id: "roadmap-1" }] })
      .mockResolvedValueOnce({ results: [] }),
    get: vi.fn().mockResolvedValue({
      id: "roadmap-1",
      title: "Frontend Engineer",
      description: "Roadmap description",
      completion_percentage: "42",
      weekly_hours_commitment: 10,
      estimated_duration_weeks: 18,
      target_level: "mid",
      journey_summary: {
        next_action_title: "Ship milestone",
        next_action_summary: "Continue the active milestone.",
        focus_label: "Active phase",
      },
      phases: [
        {
          id: "phase-1",
          title: "Core React foundations",
          description: "Strengthen the current implementation layer.",
          order: 1,
          estimated_duration_weeks: 6,
          status: "in_progress",
          completion_percentage: "50",
          objectives: [],
          milestones: [
            {
              id: "milestone-1",
              title: "Build dashboard composition",
              description: "Finish the dashboard rewrite.",
              milestone_type: "project",
              order: 1,
              estimated_duration_hours: "8",
              status: "completed",
              is_required: true,
              skills: [],
              resources: [],
            },
            {
              id: "milestone-2",
              title: "Refine roadmap interactions",
              description: "Polish the roadmap details.",
              milestone_type: "practice",
              order: 2,
              estimated_duration_hours: "6",
              status: "in_progress",
              is_required: true,
              skills: [],
              resources: [],
            },
          ],
        },
      ],
    }),
    getStats: vi.fn().mockResolvedValue({
      completed_phases: 1,
      total_phases: 4,
      completed_milestones: 2,
      total_milestones: 6,
      completed_courses: 3,
      estimated_total_hours: 40,
      roadmap_status: "in_progress",
      current_phase: {
        id: "phase-1",
        title: "Core React foundations",
        status: "in_progress",
        completion_percentage: 50,
      },
      pace: {
        current_streak_days: 3,
        total_learning_hours: 12.5,
        average_hours_per_week: 4.25,
        last_activity_date: "2026-05-03",
        on_track: true,
      },
    }),
  },
}));

import DashboardPage from "@/features/dashboard/routes/DashboardPage";
import { render } from "@/test/utils";

describe("DashboardPage", () => {
  it("renders the simplified single-column dashboard", async () => {
    render(<DashboardPage />);

    expect(await screen.findByText(/Welcome back, Mona/i)).toBeInTheDocument();

    expect(screen.getByText(/2\/6/)).toBeInTheDocument();
    expect(screen.getByText(/1\/4/)).toBeInTheDocument();
    expect(screen.getByText(/3 day/i)).toBeInTheDocument();
    expect(screen.getByText(/18w/i)).toBeInTheDocument();

    expect(screen.getAllByText(/Core React foundations/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/50%/)).toBeInTheDocument();

    expect(screen.getByText(/Refine roadmap interactions/i)).toBeInTheDocument();
  });
});
