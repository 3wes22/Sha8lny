import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render } from "@testing-library/react";

const toastSpy = vi.fn();

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: toastSpy }),
}));

vi.mock("@/lib/api", () => ({
  assessmentApi: {
    get: vi.fn().mockResolvedValue({
      id: "assessment-1",
      assessment_type: "skills",
      questions: [
        {
          id: 1,
          type: "multiple_choice",
          category: "Fundamentals",
          question: "How comfortable are you with JavaScript?",
          options: [{ value: "basic", label: "Basic", score: 2 }],
        },
      ],
      responses: [],
      presentation: { submission_state: "draft" },
    }),
    submit: vi.fn(),
  },
}));

import AssessmentSessionPage from "@/features/assessment/routes/AssessmentSessionPage";

describe("AssessmentSessionPage", () => {
  it("renders the current question", async () => {
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={["/assessment/session/assessment-1"]}
      >
        <Routes>
          <Route element={<AssessmentSessionPage />} path="/assessment/session/:assessmentId" />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/How comfortable are you with JavaScript/i)).toBeInTheDocument();
  });
});
