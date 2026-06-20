import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  listResumes: vi.fn(),
  listPortfolios: vi.fn(),
  optimizeAts: vi.fn(),
  createResume: vi.fn(),
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
    optimizeAts: mocks.optimizeAts,
    createResume: mocks.createResume,
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
  mocks.optimizeAts.mockResolvedValue({
    message: "ATS optimization analysis complete",
    ats_score: 88,
    ats_grade: "A",
    suggestions: ["Add more keywords", "Quantify achievements"],
  });
});

describe("CareerToolsPage", () => {
  it("renders resumes and portfolios", async () => {
    render(<CareerToolsPage />);

    expect(await screen.findByText("Software Engineer CV")).toBeInTheDocument();
    expect(screen.getByText("My Portfolio")).toBeInTheDocument();
  });

  it("optimizes a resume for ATS and shows suggestions", async () => {
    const user = userEvent.setup();
    render(<CareerToolsPage />);

    await screen.findByText("Software Engineer CV");

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /optimize/i }));
    });

    await waitFor(() => {
      expect(mocks.optimizeAts).toHaveBeenCalledWith("r1");
    });
    expect(await screen.findByText("Quantify achievements")).toBeInTheDocument();
  });
});
