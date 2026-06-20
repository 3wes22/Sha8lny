import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  listResumes: vi.fn(),
  listPortfolios: vi.fn(),
  improveResume: vi.fn(),
  createResume: vi.fn(),
  uploadResume: vi.fn(),
  deleteResume: vi.fn(),
  createPortfolio: vi.fn(),
  publishPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
  careerToolsApi: {
    listResumes: mocks.listResumes,
    listPortfolios: mocks.listPortfolios,
    improveResume: mocks.improveResume,
    createResume: mocks.createResume,
    uploadResume: mocks.uploadResume,
    deleteResume: mocks.deleteResume,
    createPortfolio: mocks.createPortfolio,
    publishPortfolio: mocks.publishPortfolio,
    deletePortfolio: mocks.deletePortfolio,
  },
}));

import CareerToolsPage from "@/features/career-tools/routes/CareerToolsPage";
import { render } from "@/test/utils";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.listResumes.mockResolvedValue({
    count: 1,
    results: [
      {
        id: "r1",
        title: "Software Engineer CV",
        template_name: "modern",
        is_primary: true,
        is_ats_optimized: false,
        ats_score: 72,
        ats_grade: "B",
        completeness: 80,
        version: 1,
        created_at: "2026-06-10T10:00:00Z",
        updated_at: "2026-06-12T10:00:00Z",
      },
    ],
  });
  mocks.listPortfolios.mockResolvedValue({
    count: 1,
    results: [
      {
        id: "pf1",
        title: "My Portfolio",
        is_public: false,
        view_count: 0,
        theme: "default",
        created_at: "2026-06-10T10:00:00Z",
        updated_at: "2026-06-12T10:00:00Z",
      },
    ],
  });
  mocks.improveResume.mockResolvedValue({
    ai_used: true,
    ats_score: 72,
    ats_grade: "C",
    improved_summary: "Results-driven engineer who cut latency by 40%.",
    strengthened_bullets: ["Reduced p95 latency 40% via Redis caching."],
    missing_keywords: ["CI/CD", "Kubernetes"],
    recommendations: ["Lead with measurable impact."],
  });
  mocks.uploadResume.mockResolvedValue({
    id: "r2",
    title: "uploaded-cv",
    template_name: "modern",
    is_primary: false,
    is_ats_optimized: true,
    ats_score: 75,
    ats_grade: "B",
    completeness: 60,
    ats_suggestions: { improvements: ["Add certifications"] },
    version: 1,
    created_at: "2026-06-10T10:00:00Z",
    updated_at: "2026-06-12T10:00:00Z",
  });
});

describe("CareerToolsPage", () => {
  it("renders resumes and portfolios", async () => {
    render(<CareerToolsPage />);

    expect(await screen.findByText("Software Engineer CV")).toBeInTheDocument();
    expect(screen.getByText("My Portfolio")).toBeInTheDocument();
  });

  it("improves a resume with AI and shows the suggested summary", async () => {
    const user = userEvent.setup();
    render(<CareerToolsPage />);

    await screen.findByText("Software Engineer CV");

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /improve with ai/i }));
    });

    await waitFor(() => {
      expect(mocks.improveResume).toHaveBeenCalledWith("r1");
    });
    expect(await screen.findByText(/Results-driven engineer/i)).toBeInTheDocument();
    expect(screen.getByText("CI/CD")).toBeInTheDocument();
  });

  it("copies all AI suggestions to the clipboard", async () => {
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText");
    render(<CareerToolsPage />);

    await screen.findByText("Software Engineer CV");

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /improve with ai/i }));
    });
    const copyAll = await screen.findByRole("button", { name: /copy all suggestions/i });

    await act(async () => {
      await user.click(copyAll);
    });

    await waitFor(() => {
      expect(writeText).toHaveBeenCalled();
    });
    const copied = writeText.mock.calls[0][0] as string;
    expect(copied).toContain("Results-driven engineer who cut latency by 40%.");
    expect(copied).toContain("CI/CD");
  });

  it("uploads a CV file from the upload tab", async () => {
    const user = userEvent.setup();
    render(<CareerToolsPage />);

    await screen.findByText("Software Engineer CV");

    const file = new File(["Mohamed Wes\nmohamed@example.com"], "cv.txt", { type: "text/plain" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      await user.upload(input, file);
    });

    await waitFor(() => {
      expect(mocks.uploadResume).toHaveBeenCalledWith(file);
    });
  });
});
