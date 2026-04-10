import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

const mocks = vi.hoisted(() => ({
  getResult: vi.fn(),
  createAI: vi.fn(),
  navigate: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    assessmentApi: {
      getResult: mocks.getResult,
    },
    roadmapApi: {
      createAI: mocks.createAI,
    },
  };
});

import AssessmentResultsPage from "@/features/assessment/routes/AssessmentResultsPage";

describe("AssessmentResultsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getResult.mockResolvedValue({
      id: "result-1",
      assessment: "assessment-1",
      overall_score: 80,
      strengths: ["Problem solving"],
      areas_for_improvement: ["System design"],
      recommended_careers: [{ title: "Backend Developer", match_score: 88, reasoning: "Good fit" }],
      recommended_learning_paths: [],
      ai_insights: "Solid baseline",
      llm_model_used: "mock-v1",
      total_tokens_used: 0,
      top_skills: [{ skill: "React", score: 80, category: "frontend" }],
      submission_state: "completed",
      status_message: "Your assessment is ready.",
      version: "v1",
      is_shared: false,
      created_at: "2026-04-04T12:00:00Z",
    });
    mocks.createAI.mockResolvedValue({ id: "roadmap-1" });
  });

  it("renders the assessment result hero", async () => {
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={["/assessment/results/assessment-1"]}
      >
        <Routes>
          <Route element={<AssessmentResultsPage />} path="/assessment/results/:assessmentId" />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Your assessment is ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Problem solving/i)).toBeInTheDocument();
  });

  it("creates a personalized roadmap from the completed assessment", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={["/assessment/results/assessment-1"]}
      >
        <Routes>
          <Route element={<AssessmentResultsPage />} path="/assessment/results/:assessmentId" />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(await screen.findByRole("button", { name: /generate personalized roadmap/i }));

    await waitFor(() => {
      expect(mocks.createAI).toHaveBeenCalledWith({ assessment_id: "result-1" });
    });
    expect(mocks.navigate).toHaveBeenCalledWith("/roadmap");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate personalized roadmap/i })).not.toBeDisabled();
    });
  });
});
