import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

vi.mock("@/lib/api", () => ({
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
  roadmapTemplateApi: {
    list: vi.fn().mockResolvedValue({
      results: [
        {
          id: "template-1",
          title: "Frontend",
          description: "Frontend track",
          short_description: "Frontend track",
          target_career: "Frontend Engineer",
          estimated_duration_weeks: 18,
          difficulty_level: "intermediate",
        },
      ],
    }),
  },
  roadmapApi: {
    list: vi.fn().mockResolvedValue({ results: [] }),
    get: vi.fn(),
    createFromTemplate: vi.fn(),
    activate: vi.fn(),
  },
}));

import RoadmapPage from "@/features/roadmap/routes/RoadmapPage";
import { render } from "@/test/utils";

describe("RoadmapPage", () => {
  it("renders the roadmap template chooser", async () => {
    render(<RoadmapPage />);

    expect(await screen.findByText(/Career roadmap/i)).toBeInTheDocument();
    expect(screen.getByText(/Frontend Engineer/i)).toBeInTheDocument();
  });
});
