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

  it("renders a collapsible Sources block for a grounded answer", async () => {
    mocks.chat.mockReset();
    mocks.chat.mockResolvedValueOnce({
      conversation_id: "conversation-1",
      response: "Backend roles pay competitively in Egypt.",
      delay_ms: 200,
      no_retrieval_context: false,
      retrieved_documents: [
        {
          source: "bls_ooh",
          url: "https://www.bls.gov/ooh/example.htm",
          section: "Pay",
          excerpt: "Backend engineers earn competitive salaries.",
          confidence_tier: "HIGH",
        },
      ],
      metadata: { source: "llm", processing_time_ms: 200, model: "gemini", fallback_used: false },
    });
    const user = userEvent.setup();

    render(<AdvisoryPage />);

    await act(async () => {
      await user.type(
        screen.getByPlaceholderText(/Ask about next steps, job fit, or how to approach your roadmap/i),
        "What do backend engineers earn?",
      );
      await user.click(screen.getByRole("button"));
    });

    const sourcesToggle = await screen.findByRole("button", { name: /Sources \(1\)/i });
    await act(async () => {
      await user.click(sourcesToggle);
    });

    expect(await screen.findByText(/Backend engineers earn competitive salaries\./i)).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View source/i })).toHaveAttribute(
      "href",
      "https://www.bls.gov/ooh/example.htm",
    );
  });

  it("shows the no-context state when the answer is ungrounded", async () => {
    mocks.chat.mockReset();
    mocks.chat.mockResolvedValueOnce({
      conversation_id: "conversation-1",
      response: "Here is some general guidance.",
      delay_ms: 200,
      no_retrieval_context: true,
      retrieved_documents: [],
      metadata: { source: "fallback", processing_time_ms: 200, model: null, fallback_used: true },
    });
    const user = userEvent.setup();

    render(<AdvisoryPage />);

    await act(async () => {
      await user.type(
        screen.getByPlaceholderText(/Ask about next steps, job fit, or how to approach your roadmap/i),
        "Tell me about quantum tunnels.",
      );
      await user.click(screen.getByRole("button"));
    });

    expect(await screen.findByText(/I don’t have grounded sources on that yet/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Sources \(/i })).not.toBeInTheDocument();
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
