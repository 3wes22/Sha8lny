import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";

vi.mock("@/lib/api", () => ({
  jobApi: {
    getSavedJobs: vi.fn().mockResolvedValue([]),
    search: vi.fn().mockResolvedValue({
      results: [
        {
          id: "job-1",
          title: "Frontend Engineer",
          company_name: "Atlas Labs",
          location: "Cairo, Egypt",
          job_type: "full_time",
          experience_level: "mid",
          posted_date: "2026-04-04",
          is_remote: true,
        },
      ],
    }),
    toggleSaveJob: vi.fn(),
  },
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
}));

import JobsPage from "@/features/jobs/routes/JobsPage";
import { render } from "@/test/utils";

describe("JobsPage", () => {
  it("renders job search results", async () => {
    render(<JobsPage />);

    expect(await screen.findByText(/Frontend Engineer/i)).toBeInTheDocument();
  });
});
