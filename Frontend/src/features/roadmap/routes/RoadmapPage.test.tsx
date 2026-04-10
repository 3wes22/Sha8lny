import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  roadmapTemplateList: vi.fn(),
  roadmapList: vi.fn(),
  roadmapGet: vi.fn(),
  roadmapCreateFromTemplate: vi.fn(),
  roadmapActivate: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
  roadmapTemplateApi: {
    list: mocks.roadmapTemplateList,
  },
  roadmapApi: {
    list: mocks.roadmapList,
    get: mocks.roadmapGet,
    createFromTemplate: mocks.roadmapCreateFromTemplate,
    activate: mocks.roadmapActivate,
  },
}));

import RoadmapPage from "@/features/roadmap/routes/RoadmapPage";
import { render } from "@/test/utils";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.roadmapTemplateList.mockResolvedValue({
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
  });
});

describe("RoadmapPage", () => {
  it("renders the roadmap template chooser", async () => {
    mocks.roadmapList
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] });

    render(<RoadmapPage />);

    expect(await screen.findByText(/Career roadmap/i)).toBeInTheDocument();
    expect(screen.getByText(/Frontend Engineer/i)).toBeInTheDocument();
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(1, { status: "in_progress" });
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(2, { status: "active" });
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(3, { status: "draft" });
  });

  it("reloads the latest draft roadmap when no active roadmap exists", async () => {
    mocks.roadmapList
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({
        results: [
          {
            id: "roadmap-draft-1",
            status: "draft",
          },
        ],
      });
    mocks.roadmapGet.mockResolvedValue({
      id: "roadmap-draft-1",
      title: "Frontend Engineer",
      description: "Draft roadmap description",
      status: "draft",
      completion_percentage: "0",
      total_phases: 0,
      phases: [],
    });

    render(<RoadmapPage />);

    expect(await screen.findByText(/Draft roadmap description/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Activate roadmap/i })).toBeInTheDocument();
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(1, { status: "in_progress" });
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(2, { status: "active" });
    expect(mocks.roadmapList).toHaveBeenNthCalledWith(3, { status: "draft" });
  });

  it("prefers the in-progress roadmap before checking lower-priority states", async () => {
    mocks.roadmapList.mockResolvedValueOnce({
      results: [
        {
          id: "roadmap-in-progress-1",
          status: "in_progress",
        },
      ],
    });
    mocks.roadmapGet.mockResolvedValue({
      id: "roadmap-in-progress-1",
      title: "Frontend Engineer",
      description: "In-progress roadmap description",
      status: "in_progress",
      completion_percentage: "12",
      total_phases: 3,
      phases: [],
    });

    render(<RoadmapPage />);

    expect(await screen.findByText(/In-progress roadmap description/i)).toBeInTheDocument();
    expect(mocks.roadmapList).toHaveBeenCalledTimes(1);
    expect(mocks.roadmapList).toHaveBeenCalledWith({ status: "in_progress" });
  });
});
