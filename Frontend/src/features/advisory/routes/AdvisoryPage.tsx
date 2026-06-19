import { useState } from "react";
import { Info, Loader2, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { advisorApi, type ChatRequest, type Citation } from "@/lib/api";
import { MessageSources } from "@/features/advisory/components/MessageSources";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
  noRetrievalContext?: boolean;
}

const ADVISORY_UNAVAILABLE_MESSAGE =
  "The advisor is temporarily unavailable. Keep moving with your roadmap and try this question again in a moment.";

export default function AdvisoryPage() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "intro",
      role: "assistant",
      content: "Ask about career direction, roadmap choices, or job strategy and I’ll help you reason through the next move.",
    },
  ]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: String(Date.now()),
      role: "user",
      content: inputValue,
    };

    setMessages((previous) => [...previous, userMessage]);
    setInputValue("");
    setLoading(true);

    try {
      const request: ChatRequest = {
        message: userMessage.content,
        ...(conversationId ? { conversation_id: conversationId } : {}),
        conversation_history: messages
          .filter((message) => message.id !== "intro")
          .map((message) => ({ role: message.role, content: message.content })),
      };

      const response = await advisorApi.chat(request);
      setConversationId(response.conversation_id);
      setMessages((previous) => [
        ...previous,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: response.response,
          sources: response.retrieved_documents ?? [],
          noRetrievalContext: response.no_retrieval_context ?? false,
        },
      ]);
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          id: `${Date.now()}-fallback`,
          role: "assistant",
          content: ADVISORY_UNAVAILABLE_MESSAGE,
        },
      ]);
      toast({
        title: "Advisor unavailable",
        description: "Could not reach the advisory service.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell
      description="This surface stays calmer than marketing but still feels intentional and modern."
      eyebrow="Advisory"
      title="Career advisor"
      aside={
        <StatePanel
          description="The advisory surface currently uses request-response messaging. A future websocket upgrade can stream richer answers into this same shell."
          state="processing"
          title="Realtime upgrade pending"
        />
      }
    >
      <div className="atlas-panel flex min-h-[520px] flex-col p-6">
        <div className="flex-1 space-y-4 overflow-y-auto">
          {messages.map((message) => (
            <div
              className={`max-w-[80%] rounded-[1.5rem] p-4 ${
                message.role === "assistant"
                  ? "bg-muted/50"
                  : "ml-auto bg-primary text-primary-foreground"
              }`}
              key={message.id}
            >
              <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
              {message.role === "assistant" && message.noRetrievalContext ? (
                <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Info className="h-3.5 w-3.5" />
                  I don’t have grounded sources on that yet, so this is general guidance — not retrieved facts.
                </p>
              ) : null}
              {message.role === "assistant" && message.sources && message.sources.length > 0 ? (
                <MessageSources sources={message.sources} />
              ) : null}
            </div>
          ))}
        </div>
        <div className="mt-6 flex gap-3">
          <Textarea
            className="min-h-[90px]"
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Ask about next steps, job fit, or how to approach your roadmap..."
            value={inputValue}
          />
          <Button className="gradient-primary px-5" disabled={loading} onClick={handleSend}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </PageShell>
  );
}
