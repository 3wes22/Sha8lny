import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AdvisoryPage from "@/features/advisory/routes/AdvisoryPage";
import { render } from "@/test/utils";

const mocks = vi.hoisted(() => ({
  chat: vi.fn(),
  toast: vi.fn(),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: mocks.toast,
  }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    advisorApi: {
      chat: mocks.chat,
    },
  };
});

describe("AdvisoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.chat
      .mockResolvedValueOnce({
        conversation_id: "conversation-1",
        response: "Start with one portfolio project.",
        delay_ms: 200,
        metadata: {
          source: "baseline",
          processing_time_ms: 200,
          model: "baseline-advisor-v1",
          trace_id: "trace-1",
          fallback_used: false,
        },
      })
      .mockResolvedValueOnce({
        conversation_id: "conversation-1",
        response: "Then tighten your resume around that proof of work.",
        delay_ms: 220,
        metadata: {
          source: "baseline",
          processing_time_ms: 220,
          model: "baseline-advisor-v1",
          trace_id: "trace-2",
          fallback_used: false,
        },
      });
  });

  it("reuses the backend conversation id for follow-up messages", async () => {
    const user = userEvent.setup();

    render(<AdvisoryPage />);

    await act(async () => {
      await user.type(
        screen.getByPlaceholderText(/Ask about next steps, job fit, or how to approach your roadmap/i),
        "What should I focus on next?",
      );
      await user.click(screen.getByRole("button"));
    });

    await waitFor(() => {
      expect(mocks.chat).toHaveBeenCalledWith({
        message: "What should I focus on next?",
        conversation_history: [],
      });
    });
    expect(await screen.findByText(/Start with one portfolio project\./i)).toBeInTheDocument();

    await act(async () => {
      await user.type(
        screen.getByPlaceholderText(/Ask about next steps, job fit, or how to approach your roadmap/i),
        "What after that?",
      );
      await user.click(screen.getByRole("button"));
    });

    await waitFor(() => {
      expect(mocks.chat).toHaveBeenLastCalledWith({
        message: "What after that?",
        conversation_id: "conversation-1",
        conversation_history: [
          { role: "user", content: "What should I focus on next?" },
          { role: "assistant", content: "Start with one portfolio project." },
        ],
      });
    });
    expect(await screen.findByText(/tighten your resume around that proof of work/i)).toBeInTheDocument();
  });

  it("shows an in-chat fallback message when the advisory request fails", async () => {
    mocks.chat.mockReset();
    mocks.chat.mockRejectedValueOnce(new Error("offline"));
    const user = userEvent.setup();

    render(<AdvisoryPage />);

    await act(async () => {
      await user.type(
        screen.getByPlaceholderText(/Ask about next steps, job fit, or how to approach your roadmap/i),
        "Help me decide what to do next.",
      );
      await user.click(screen.getByRole("button"));
    });

    expect(await screen.findByText(/advisor is temporarily unavailable/i)).toBeInTheDocument();
    expect(mocks.toast).toHaveBeenCalled();
  });
});
