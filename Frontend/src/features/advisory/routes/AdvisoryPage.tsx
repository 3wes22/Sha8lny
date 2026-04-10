import { useState } from "react";
import { Loader2, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { advisorApi, type ChatRequest } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

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
        { id: `${Date.now()}-assistant`, role: "assistant", content: response.response },
      ]);
    } catch {
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
