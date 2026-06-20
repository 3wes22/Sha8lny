import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { RoadmapMilestone } from "@/lib/api";
import { RoadmapMilestoneRow } from "@/features/roadmap/components/RoadmapMilestoneRow";
import { render } from "@/test/utils";

const milestone = (overrides: Partial<RoadmapMilestone> = {}): RoadmapMilestone =>
  ({
    id: "m1",
    title: "Learn React fundamentals",
    description: "",
    milestone_type: "course",
    order: 1,
    estimated_duration_hours: "6",
    status: "not_started",
    is_required: true,
    skills: [],
    resources: [],
    ...overrides,
  }) as RoadmapMilestone;

describe("RoadmapMilestoneRow", () => {
  it("renders the milestone title, type, and estimated hours", () => {
    render(<RoadmapMilestoneRow milestone={milestone()} onToggle={vi.fn()} />);

    expect(screen.getByText("Learn React fundamentals")).toBeInTheDocument();
    expect(screen.getByText(/course/i)).toBeInTheDocument();
    expect(screen.getByText(/6h/i)).toBeInTheDocument();
  });

  it("reflects a completed milestone as checked", () => {
    render(<RoadmapMilestoneRow milestone={milestone({ status: "completed" })} onToggle={vi.fn()} />);

    expect(screen.getByRole("checkbox", { name: /Learn React fundamentals/i })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("calls onToggle with the milestone when clicked", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    const target = milestone();

    render(<RoadmapMilestoneRow milestone={target} onToggle={onToggle} />);
    await user.click(screen.getByRole("checkbox", { name: /Learn React fundamentals/i }));

    expect(onToggle).toHaveBeenCalledWith(target);
  });

  it("does not call onToggle when disabled", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();

    render(<RoadmapMilestoneRow disabled milestone={milestone()} onToggle={onToggle} />);
    await user.click(screen.getByRole("checkbox", { name: /Learn React fundamentals/i }));

    expect(onToggle).not.toHaveBeenCalled();
  });
});

const baseMilestone: RoadmapMilestone = {
  id: "m1",
  title: "Learn HTTP basics",
  description: "",
  milestone_type: "course",
  order: 1,
  estimated_duration_hours: "10.00",
  status: "completed",
  is_required: true,
  skills: [],
  resources: [],
  completed_from_assessment: true,
};

describe("RoadmapMilestoneRow assessment baseline", () => {
  it("labels assessment-derived completions and offers Revise", () => {
    render(<RoadmapMilestoneRow milestone={baseMilestone} onToggle={() => {}} />);
    expect(screen.getByText(/from your assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/revise/i)).toBeInTheDocument();
  });

  it("calls onToggle when an assessment row is clicked (to reopen)", () => {
    const onToggle = vi.fn();
    render(<RoadmapMilestoneRow milestone={baseMilestone} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith(baseMilestone);
  });
});
