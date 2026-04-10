import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, getApiErrorMessage, userApi } from "@/lib/api";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("userApi contract helpers", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("uses PATCH for partial profile updates", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        id: "user-1",
        username: "mona",
        full_name: "Updated Name",
        email: "mona@example.com",
        is_premium: false,
        onboarding_completed: true,
        preferred_language: "en",
        created_at: "2026-04-05T00:00:00Z",
      }),
    );

    await userApi.updateProfile({ full_name: "Updated Name" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/users/me/");
    expect(init?.method).toBe("PATCH");
    expect(init?.body).toBe(JSON.stringify({ full_name: "Updated Name" }));
  });

  it("posts skill_id with a string proficiency when adding skills", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        {
          id: "user-skill-1",
          skill: { id: "skill-1", name: "React", category: "frontend" },
          proficiency_level: "intermediate",
          is_verified: false,
        },
        201,
      ),
    );

    await userApi.addSkill("skill-1", "intermediate");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/users/user-skills/");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(
      JSON.stringify({
        skill_id: "skill-1",
        proficiency_level: "intermediate",
      }),
    );
  });

  it("surfaces the first backend validation detail from wrapped error payloads", () => {
    const error = new ApiError(
      400,
      "Bad Request",
      {
        error: true,
        code: "validation_error",
        message: "Validation failed",
        details: {
          password: ["This password is too common."],
        },
      },
      "http://localhost:8000/api/v1/users/auth/register/",
    );

    expect(getApiErrorMessage(error, "Registration failed. Please try again.")).toBe(
      "This password is too common.",
    );
  });
});
