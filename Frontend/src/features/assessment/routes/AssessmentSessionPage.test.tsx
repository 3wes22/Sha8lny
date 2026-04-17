import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  assessmentGet: vi.fn(),
  assessmentSubmit: vi.fn(),
}));

const toastSpy = vi.fn();

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: toastSpy }),
}));

vi.mock("@/lib/api", () => ({
  assessmentApi: {
    get: mocks.assessmentGet,
    submit: mocks.assessmentSubmit,
  },
}));

import AssessmentSessionPage from "@/features/assessment/routes/AssessmentSessionPage";

async function flushAssessmentEffects() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("AssessmentSessionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it("polls until generated questions are ready", async () => {
    vi.useFakeTimers();

    mocks.assessmentGet
      .mockResolvedValueOnce({
        id: "assessment-1",
        assessment_type: "skills",
        stage: "stage_1",
        active_questions: [],
        questions: [],
        responses: [],
        generation_status: "pending",
        ai_processing_status: "pending",
        presentation: { submission_state: "stage_1_generating" },
      })
      .mockResolvedValueOnce({
        id: "assessment-1",
        assessment_type: "skills",
        stage: "stage_1",
        active_questions: [
          {
            id: "s1_q1",
            type: "multiple_choice",
            category: "Fundamentals",
            question: "How comfortable are you with JavaScript?",
            options: [{ value: "basic", label: "Basic", score: 2 }],
          },
        ],
        questions: [
          {
            id: "s1_q1",
            type: "multiple_choice",
            category: "Fundamentals",
            question: "How comfortable are you with JavaScript?",
            options: [{ value: "basic", label: "Basic", score: 2 }],
          },
        ],
        responses: [],
        generation_status: "completed",
        ai_processing_status: "completed",
        presentation: { submission_state: "stage_1_ready" },
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

    await flushAssessmentEffects();
    expect(screen.getByText(/Preparing assessment/i)).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mocks.assessmentGet).toHaveBeenCalledTimes(2);
    expect(screen.getByText(/How comfortable are you with JavaScript/i)).toBeInTheDocument();
  });

  it("renders the current question", async () => {
    mocks.assessmentGet.mockResolvedValue({
      id: "assessment-1",
      assessment_type: "skills",
      stage: "stage_1",
      active_questions: [
        {
          id: "s1_q1",
          type: "multiple_choice",
          category: "Fundamentals",
          question: "How comfortable are you with JavaScript?",
          options: [{ value: "basic", label: "Basic", score: 2 }],
        },
      ],
      questions: [
        {
          id: "s1_q1",
          type: "multiple_choice",
          category: "Fundamentals",
          question: "How comfortable are you with JavaScript?",
          options: [{ value: "basic", label: "Basic", score: 2 }],
        },
      ],
      responses: [],
      generation_status: "completed",
      ai_processing_status: "completed",
      presentation: { submission_state: "stage_1_ready" },
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

  it("submits stage one, shows analyzing, and then renders stage two questions", async () => {
    vi.useFakeTimers();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    mocks.assessmentGet
      .mockResolvedValueOnce({
        id: "assessment-1",
        assessment_type: "skills",
        stage: "stage_1",
        active_questions: [
          {
            id: "s1_q1",
            type: "multiple_choice",
            category: "API Design",
            question: "How comfortable are you with API design?",
            options: [{ value: "mid", label: "Mid", score: 3 }],
          },
        ],
        questions: [
          {
            id: "s1_q1",
            type: "multiple_choice",
            category: "API Design",
            question: "How comfortable are you with API design?",
            options: [{ value: "mid", label: "Mid", score: 3 }],
          },
        ],
        responses: [],
        generation_status: "completed",
        ai_processing_status: "completed",
        presentation: { submission_state: "stage_1_ready" },
      })
      .mockResolvedValueOnce({
        id: "assessment-1",
        assessment_type: "skills",
        stage: "stage_2",
        active_questions: [
          {
            id: "s2_q1",
            type: "multiple_choice",
            category: "Databases",
            question: "How do you reason about schema tradeoffs?",
            options: [{ value: "mid", label: "Mid", score: 3 }],
          },
        ],
        questions: [
          {
            id: "s2_q1",
            type: "multiple_choice",
            category: "Databases",
            question: "How do you reason about schema tradeoffs?",
            options: [{ value: "mid", label: "Mid", score: 3 }],
          },
        ],
        responses: [],
        generation_status: "completed",
        ai_processing_status: "completed",
        presentation: { submission_state: "stage_2_ready" },
      });

    mocks.assessmentSubmit.mockResolvedValue({
      assessment: {
        id: "assessment-1",
        assessment_type: "skills",
        stage: "stage_1",
        active_questions: [],
        questions: [],
        responses: [],
        generation_status: "processing",
        ai_processing_status: "processing",
        presentation: { submission_state: "stage_1_analyzing" },
      },
      submission_state: "stage_1_analyzing",
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

    await flushAssessmentEffects();

    await user.click(screen.getByText("Mid"));
    await act(async () => {
      await user.click(screen.getByRole("button", { name: /submit assessment/i }));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText(/Analyzing your responses/i)).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mocks.assessmentGet).toHaveBeenCalledTimes(2);
    expect(screen.getByText(/How do you reason about schema tradeoffs/i)).toBeInTheDocument();
  });
});
