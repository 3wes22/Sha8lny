import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  getStats: vi.fn(),
  completions: vi.fn(),
  recentAchievements: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
  progressApi: {
    getStats: mocks.getStats,
    completions: mocks.completions,
    recentAchievements: mocks.recentAchievements,
  },
}));

import ProgressPage from "@/features/progress/routes/ProgressPage";
import { render } from "@/test/utils";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.getStats.mockResolvedValue({
    total_learning_hours: "42.5",
    total_courses_completed: 3,
    total_milestones_achieved: 7,
    current_streak_days: 5,
    longest_streak_days: 12,
    roadmaps_in_progress: 1,
    roadmaps_completed: 0,
    average_daily_hours: "1.4",
    this_week_hours: "6.0",
    last_activity_date: "2026-06-19",
  });
  mocks.recentAchievements.mockResolvedValue([
    {
      id: "a1",
      milestone: "m1",
      milestone_title: "Finished Python Basics",
      achieved_at: "2026-06-18T10:00:00Z",
      badge_awarded: true,
      badge_type: "gold",
    },
  ]);
  mocks.completions.mockResolvedValue({
    count: 1,
    results: [
      {
        id: "cc1",
        course: "c1",
        course_title: "Intro to SQL",
        completed_at: "2026-06-15T10:00:00Z",
        completion_percentage: 100,
        rating_display: "5/5",
        has_certificate: true,
      },
    ],
  });
});

describe("ProgressPage", () => {
  it("renders progress statistics", async () => {
    render(<ProgressPage />);

    expect(await screen.findByText("42.5")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("renders recent achievements and course completions", async () => {
    render(<ProgressPage />);

    expect(await screen.findByText("Finished Python Basics")).toBeInTheDocument();
    expect(screen.getByText("Intro to SQL")).toBeInTheDocument();
  });
});
