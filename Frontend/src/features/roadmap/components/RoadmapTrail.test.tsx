import { describe, expect, it, vi } from "vitest";
import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Roadmap, RoadmapMilestone, RoadmapPhase } from "@/lib/api";
import { RoadmapTrail } from "@/features/roadmap/components/RoadmapTrail";
import { render } from "@/test/utils";

const milestone = (id: string, title: string): RoadmapMilestone =>
  ({
    id,
    title,
    description: "",
    milestone_type: "course",
    order: 1,
    estimated_duration_hours: "5",
    status: "not_started",
    is_required: true,
    skills: [],
    resources: [],
  }) as RoadmapMilestone;

const phase = (
  id: string,
  title: string,
  status: RoadmapPhase["status"],
  milestones: RoadmapMilestone[],
  order: number,
): RoadmapPhase =>
  ({
    id,
    title,
    description: `${title} description`,
    order,
    estimated_duration_weeks: 3,
    status,
    completion_percentage: "0",
    objectives: [],
    milestones,
  }) as RoadmapPhase;

const roadmap = (): Roadmap =>
  ({
    id: "r1",
    title: "Frontend Developer",
    description: "",
    status: "in_progress",
    completion_percentage: "30",
    phases: [
      phase("p1", "Foundations", "completed", [milestone("m0", "HTML basics")], 1),
      phase("p2", "Frameworks", "in_progress", [milestone("m1", "React basics")], 2),
      phase("p3", "Specialization", "not_started", [milestone("m2", "State management")], 3),
      phase("p4", "Portfolio", "not_started", [milestone("m3", "Build portfolio")], 4),
    ],
  }) as Roadmap;

describe("RoadmapTrail", () => {
  it("renders a station for every phase", () => {
    render(<RoadmapTrail onMilestoneToggle={vi.fn()} roadmap={roadmap()} />);

    expect(screen.getByText("Foundations")).toBeInTheDocument();
    expect(screen.getByText("Frameworks")).toBeInTheDocument();
    expect(screen.getByText("Specialization")).toBeInTheDocument();
    expect(screen.getByText("Portfolio")).toBeInTheDocument();
  });

  it("expands the current phase by default", () => {
    render(<RoadmapTrail onMilestoneToggle={vi.fn()} roadmap={roadmap()} />);

    expect(screen.getByText("React basics")).toBeInTheDocument();
    expect(screen.queryByText("State management")).not.toBeInTheDocument();
  });

  it("opens another station when its header is clicked and collapses the previous one", async () => {
    const user = userEvent.setup();
    render(<RoadmapTrail onMilestoneToggle={vi.fn()} roadmap={roadmap()} />);

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /Specialization/i }));
    });

    expect(screen.getByText("State management")).toBeInTheDocument();
    expect(screen.queryByText("React basics")).not.toBeInTheDocument();
  });

  it("renders an empty state when the roadmap has no phases", () => {
    render(<RoadmapTrail onMilestoneToggle={vi.fn()} roadmap={{ ...roadmap(), phases: [] }} />);

    expect(screen.getByText(/no phases/i)).toBeInTheDocument();
  });
});
