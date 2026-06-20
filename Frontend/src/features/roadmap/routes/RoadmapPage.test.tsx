import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  roadmapTemplateList: vi.fn(),
  roadmapList: vi.fn(),
  roadmapGet: vi.fn(),
  roadmapCreateFromTemplate: vi.fn(),
  roadmapActivate: vi.fn(),
  roadmapUpdateProgress: vi.fn(),
  navigate: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

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
    updateProgress: mocks.roadmapUpdateProgress,
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

  it("polls until a pending roadmap finishes generating", async () => {
    mocks.roadmapList
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [{ id: "roadmap-draft-1", status: "draft" }] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [{ id: "roadmap-draft-1", status: "draft" }] });
    mocks.roadmapGet
      .mockResolvedValueOnce({
        id: "roadmap-draft-1",
        title: "Backend Engineer",
        description: "Roadmap shell",
        status: "draft",
        ai_processing_status: "pending",
        completion_percentage: "0",
        total_phases: 0,
        phases: [],
      })
      .mockResolvedValueOnce({
        id: "roadmap-draft-1",
        title: "Backend Engineer",
        description: "Personalized roadmap description",
        status: "draft",
        ai_processing_status: "completed",
        completion_percentage: "0",
        total_phases: 3,
        phases: [],
      });

    render(<RoadmapPage />);

    expect(await screen.findByText(/Creating roadmap/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mocks.roadmapGet).toHaveBeenCalledTimes(2);
    }, { timeout: 3000 });

    expect(await screen.findByText(/Personalized roadmap description/i)).toBeInTheDocument();
  });

  it("toggles a milestone in the trail and persists it via updateProgress", async () => {
    const user = userEvent.setup();

    mocks.roadmapList.mockResolvedValueOnce({
      results: [{ id: "roadmap-trail-1", status: "in_progress" }],
    });
    mocks.roadmapGet.mockResolvedValue({
      id: "roadmap-trail-1",
      title: "Frontend Engineer",
      description: "Trail roadmap description",
      status: "in_progress",
      ai_processing_status: "completed",
      completion_percentage: "20",
      total_phases: 1,
      phases: [
        {
          id: "phase-1",
          title: "Frameworks",
          description: "React",
          order: 1,
          estimated_duration_weeks: 3,
          status: "in_progress",
          completion_percentage: "0",
          objectives: [],
          milestones: [
            {
              id: "milestone-1",
              title: "Learn React fundamentals",
              description: "",
              milestone_type: "course",
              order: 1,
              estimated_duration_hours: "6",
              status: "not_started",
              is_required: true,
              skills: [],
              resources: [],
            },
          ],
        },
      ],
    });
    mocks.roadmapUpdateProgress.mockResolvedValue({});

    render(<RoadmapPage />);

    const milestone = await screen.findByRole("checkbox", { name: /Learn React fundamentals/i });
    await act(async () => {
      await user.click(milestone);
    });

    await waitFor(() => {
      expect(mocks.roadmapUpdateProgress).toHaveBeenCalledWith("roadmap-trail-1", {
        milestone_id: "milestone-1",
        status: "completed",
      });
    });
  });

  it("navigates to the dashboard after activating a draft roadmap", async () => {
    const user = userEvent.setup();

    mocks.roadmapList
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValueOnce({ results: [{ id: "roadmap-draft-1", status: "draft" }] });
    mocks.roadmapGet.mockResolvedValue({
      id: "roadmap-draft-1",
      title: "Frontend Engineer",
      description: "Draft roadmap description",
      status: "draft",
      completion_percentage: "0",
      total_phases: 0,
      phases: [],
    });
    mocks.roadmapActivate.mockResolvedValue({
      id: "roadmap-draft-1",
      title: "Frontend Engineer",
      description: "Draft roadmap description",
      status: "active",
      completion_percentage: "0",
      total_phases: 0,
      phases: [],
    });

    render(<RoadmapPage />);

    const activateButton = await screen.findByRole("button", { name: /Activate roadmap/i });
    await act(async () => {
      await user.click(activateButton);
    });

    await waitFor(() => {
      expect(mocks.roadmapActivate).toHaveBeenCalledWith("roadmap-draft-1");
      expect(mocks.navigate).toHaveBeenCalledWith("/dashboard");
    });
  });
});
