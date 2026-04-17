import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  navigate: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  assessmentApi: {
    create: mocks.create,
  },
}));

import AssessmentPage from "@/features/assessment/routes/AssessmentPage";

describe("AssessmentPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.create.mockResolvedValue({ id: "assessment-1" });
  });

  it("starts a staged skills assessment from a supported path", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
        <AssessmentPage />
      </MemoryRouter>,
    );

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /Backend Developer/i }));
    });

    await waitFor(() => {
      expect(mocks.create).toHaveBeenCalledWith({
        assessment_type: "skills",
        target_career: "Backend Developer",
      });
      expect(mocks.navigate).toHaveBeenCalledWith("/assessment/session/assessment-1");
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Backend Developer/i })).not.toBeDisabled();
    });
  });
});
