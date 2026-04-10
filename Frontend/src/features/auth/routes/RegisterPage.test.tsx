import { describe, expect, it, vi } from "vitest";

import { render, screen } from "@/test/utils";
import RegisterPage from "@/features/auth/routes/RegisterPage";

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: () => ({
    register: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("RegisterPage", () => {
  it("provides browser autocomplete hints for registration fields", () => {
    render(<RegisterPage />);

    expect(screen.getByLabelText(/username/i)).toHaveAttribute("autocomplete", "username");
    expect(screen.getByLabelText(/full name/i)).toHaveAttribute("autocomplete", "name");
    expect(screen.getByLabelText(/^email$/i)).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute("autocomplete", "new-password");
    expect(screen.getByLabelText(/confirm password/i)).toHaveAttribute("autocomplete", "new-password");
    expect(screen.getByLabelText(/date of birth/i)).toHaveAttribute("autocomplete", "bday");
  });
});
