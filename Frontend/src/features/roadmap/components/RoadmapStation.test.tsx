import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { RoadmapMilestone, RoadmapPhase } from "@/lib/api";
import { RoadmapStation } from "@/features/roadmap/components/RoadmapStation";
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

const phase = (overrides: Partial<RoadmapPhase> = {}): RoadmapPhase =>
  ({
    id: "phase-1",
    title: "Frameworks & Tooling",
    description: "React and build tools",
    order: 3,
    estimated_duration_weeks: 4,
    status: "in_progress",
    completion_percentage: "40",
    objectives: [],
    milestones: [milestone("m1", "Learn React fundamentals")],
    ...overrides,
  }) as RoadmapPhase;

const baseProps = {
  index: 2,
  state: "current" as const,
  expanded: true,
  isLast: false,
  onToggleExpand: vi.fn(),
  onMilestoneToggle: vi.fn(),
};

describe("RoadmapStation", () => {
  it("renders the phase title", () => {
    render(<RoadmapStation {...baseProps} phase={phase()} />);
    expect(screen.getByText("Frameworks & Tooling")).toBeInTheDocument();
  });

  it("shows milestone rows when expanded", () => {
    render(<RoadmapStation {...baseProps} expanded phase={phase()} />);
    expect(screen.getByText("Learn React fundamentals")).toBeInTheDocument();
  });

  it("hides milestone rows when collapsed", () => {
    render(<RoadmapStation {...baseProps} expanded={false} phase={phase({ status: "completed" })} state="completed" />);
    expect(screen.queryByText("Learn React fundamentals")).not.toBeInTheDocument();
  });

  it("calls onToggleExpand when a non-locked station header is clicked", async () => {
    const user = userEvent.setup();
    const onToggleExpand = vi.fn();

    render(
      <RoadmapStation {...baseProps} expanded={false} onToggleExpand={onToggleExpand} phase={phase()} />,
    );
    await user.click(screen.getByRole("button", { name: /Frameworks & Tooling/i }));

    expect(onToggleExpand).toHaveBeenCalledTimes(1);
  });

  it("does not expand a locked station and shows it is locked", async () => {
    const user = userEvent.setup();
    const onToggleExpand = vi.fn();

    render(
      <RoadmapStation
        {...baseProps}
        expanded={false}
        onToggleExpand={onToggleExpand}
        phase={phase({ status: "not_started" })}
        state="locked"
      />,
    );

    await user.click(screen.getByRole("button", { name: /Frameworks & Tooling/i }));

    expect(onToggleExpand).not.toHaveBeenCalled();
    expect(screen.getByText(/locked/i)).toBeInTheDocument();
  });

  it("shows an assessment-baseline caption on a passed station", () => {
    const phase = {
      id: "p1",
      title: "Foundations: Backend Developer",
      description: "",
      order: 1,
      estimated_duration_weeks: 4,
      status: "completed" as const,
      completion_percentage: "100.00",
      objectives: [],
      milestones: [],
      baseline_from_assessment: true,
    };
    render(
      <RoadmapStation
        phase={phase}
        index={0}
        state="completed"
        expanded={false}
        onToggleExpand={() => {}}
        onMilestoneToggle={() => {}}
      />,
    );
    expect(screen.getByText(/set from your assessment/i)).toBeInTheDocument();
  });
});
