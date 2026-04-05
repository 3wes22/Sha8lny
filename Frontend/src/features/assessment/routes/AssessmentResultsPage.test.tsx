import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render } from "@testing-library/react";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    assessmentApi: {
      getResult: vi.fn().mockResolvedValue({
        id: "result-1",
        assessment: "assessment-1",
        overall_score: 80,
        strengths: ["Problem solving"],
        areas_for_improvement: ["System design"],
        recommended_careers: [],
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
      }),
    },
  };
});

import AssessmentResultsPage from "@/features/assessment/routes/AssessmentResultsPage";

describe("AssessmentResultsPage", () => {
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
});
