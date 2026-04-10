import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  assessmentGet: vi.fn(),
}));

const toastSpy = vi.fn();

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: toastSpy }),
}));

vi.mock("@/lib/api", () => ({
  assessmentApi: {
    get: mocks.assessmentGet,
    submit: vi.fn(),
  },
}));

import AssessmentSessionPage from "@/features/assessment/routes/AssessmentSessionPage";

describe("AssessmentSessionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it("polls until generated questions are ready", async () => {
    mocks.assessmentGet
      .mockResolvedValueOnce({
        id: "assessment-1",
        assessment_type: "skills",
        questions: [],
        responses: [],
        ai_processing_status: "pending",
        presentation: { submission_state: "generating" },
      })
      .mockResolvedValueOnce({
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
        ai_processing_status: "completed",
        presentation: { submission_state: "ready" },
      });

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

    expect(await screen.findByText(/Preparing assessment/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mocks.assessmentGet).toHaveBeenCalledTimes(2);
    }, { timeout: 3000 });

    await waitFor(() => {
      expect(screen.getByText(/How comfortable are you with JavaScript/i)).toBeInTheDocument();
    });
  });

  it("renders the current question", async () => {
    mocks.assessmentGet.mockResolvedValue({
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
      ai_processing_status: "completed",
      presentation: { submission_state: "ready" },
    });

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
