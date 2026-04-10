import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  addSkill: vi.fn(),
  getAllSkills: vi.fn(),
  getSkills: vi.fn(),
  refreshUser: vi.fn(),
  removeSkill: vi.fn(),
  toast: vi.fn(),
  updateProfile: vi.fn(),
  user: {
    username: "mona",
    full_name: "Mona Ali",
    phone_number: "",
    preferred_language: "en",
    timezone: "Africa/Cairo",
  },
}));

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: () => ({
    user: mocks.user,
    refreshUser: mocks.refreshUser,
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: mocks.toast,
  }),
}));

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  userApi: {
    addSkill: mocks.addSkill,
    getAllSkills: mocks.getAllSkills,
    getSkills: mocks.getSkills,
    removeSkill: mocks.removeSkill,
    updateProfile: mocks.updateProfile,
  },
}));

import ProfilePage from "@/features/profile/routes/ProfilePage";
import { render } from "@/test/utils";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ProfilePage", () => {
  it("renders skills from paginated users endpoints", async () => {
    mocks.getSkills.mockResolvedValue({
      results: [
        {
          id: "user-skill-1",
          skill: { id: "skill-1", name: "React", category: "frontend" },
          proficiency_level: "intermediate",
          is_verified: false,
        },
      ],
    });
    mocks.getAllSkills.mockResolvedValue({
      results: [{ id: "skill-1", name: "React", category: "frontend" }],
    });

    render(<ProfilePage />);

    expect(await screen.findByText(/React · level intermediate/i)).toBeInTheDocument();
    expect(screen.getByText(/^1$/)).toBeInTheDocument();
  });

  it("adds a matched skill with the backend proficiency contract", async () => {
    mocks.getSkills.mockResolvedValue({ results: [] });
    mocks.getAllSkills.mockResolvedValue({
      results: [{ id: "skill-1", name: "React", category: "frontend" }],
    });
    mocks.addSkill.mockResolvedValue({
      id: "user-skill-1",
      skill: { id: "skill-1", name: "React", category: "frontend" },
      proficiency_level: "intermediate",
      is_verified: false,
    });

    render(<ProfilePage />);

    expect(await screen.findByText(/No skills attached yet/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Add skill/i), {
      target: { value: "React" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Add skill/i }));
    });

    expect(mocks.addSkill).toHaveBeenCalledWith("skill-1", "intermediate");
    expect(await screen.findByText(/React · level intermediate/i)).toBeInTheDocument();
  });
});
