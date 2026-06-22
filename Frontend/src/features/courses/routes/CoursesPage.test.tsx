import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  search: vi.fn(),
  platforms: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  getApiErrorMessage: vi.fn((_, fallback) => fallback),
  courseApi: {
    search: mocks.search,
    platforms: mocks.platforms,
  },
}));

import CoursesPage from "@/features/courses/routes/CoursesPage";
import { render } from "@/test/utils";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.platforms.mockResolvedValue({ results: [{ id: "p1", name: "Udemy", slug: "udemy", is_active: true }] });
  mocks.search.mockResolvedValue({
    count: 1,
    results: [
      {
        id: "c1",
        title: "React for Beginners",
        platform_name: "Udemy",
        price: 0,
        currency: "USD",
        rating: 4.6,
        level: "beginner",
      },
    ],
  });
});

describe("CoursesPage", () => {
  it("renders courses returned from the catalog", async () => {
    render(<CoursesPage />);

    expect(await screen.findByText("React for Beginners")).toBeInTheDocument();
    expect(screen.getAllByText(/Udemy/i).length).toBeGreaterThan(0);
    expect(screen.getByText("Free")).toBeInTheDocument();
  });

  it("searches the catalog with the typed query", async () => {
    const user = userEvent.setup();
    render(<CoursesPage />);

    await screen.findByText("React for Beginners");

    const input = screen.getByPlaceholderText(/search courses/i);
    await act(async () => {
      await user.type(input, "react");
      await user.click(screen.getByRole("button", { name: /^search$/i }));
    });

    await waitFor(() => {
      expect(mocks.search).toHaveBeenLastCalledWith(expect.objectContaining({ query: "react" }));
    });
  });
});
