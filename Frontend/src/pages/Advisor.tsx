import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Send, ThumbsUp, ThumbsDown, Copy, Sparkles, Bot, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function Advisor() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "👋 Hello! I'm your AI Career Advisor. I can help you with career planning, skill development, job search strategies, and more. What would you like to discuss today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const suggestions = [
    "How do I become a data scientist?",
    "Which skills do I need for backend development?",
    "How can I transition to a tech career?",
    "What's the best way to learn React?",
  ];

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "That's a great question! Based on your profile and current skills, here's what I recommend:\n\n1. **Start with the fundamentals** - Build a strong foundation in the core concepts\n2. **Practice regularly** - Consistent practice is key to mastering any skill\n3. **Work on projects** - Apply what you learn through hands-on projects\n4. **Join communities** - Connect with others learning the same skills\n\nWould you like me to elaborate on any of these points?",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleSuggestion = (suggestion: string) => {
    setInputValue(suggestion);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({
      title: "Copied!",
      description: "Message copied to clipboard",
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl gradient-primary mb-4">
          <MessageSquare className="h-8 w-8 text-primary-foreground" />
        </div>
        <h1 className="text-4xl font-bold">AI Career Advisor</h1>
        <p className="text-muted-foreground text-lg">
          Get personalized career guidance powered by AI. Ask me anything about your career path!
        </p>
      </div>

      {/* Chat Container */}
      <Card className="min-h-[600px] flex flex-col">
        <CardContent className="flex-1 flex flex-col p-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn("flex gap-4", message.role === "user" && "flex-row-reverse")}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0",
                    message.role === "assistant"
                      ? "gradient-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground"
                  )}
                >
                  {message.role === "assistant" ? (
                    <Bot className="h-5 w-5" />
                  ) : (
                    <User className="h-5 w-5" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={`flex-1 max-w-[80%] ${
                    message.role === "user" ? "flex justify-end" : ""
                  }`}
                >
                  <div
                    className={`rounded-2xl p-4 ${
                      message.role === "assistant"
                        ? "bg-muted"
                        : "gradient-primary text-primary-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>

                  {/* Action Buttons (only for assistant messages) */}
                  {message.role === "assistant" && (
                    <div className="flex items-center gap-2 mt-2 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(message.content)}
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </Button>
                      <Button variant="ghost" size="sm">
                        <ThumbsUp className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <ThumbsDown className="h-3 w-3" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex gap-4">
                <div className="h-10 w-10 rounded-full gradient-primary flex items-center justify-center flex-shrink-0">
                  <Bot className="h-5 w-5 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-2xl p-4">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-2 h-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-2 h-2 rounded-full bg-foreground/50 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quick Suggestions */}
          {messages.length === 1 && !isTyping && (
            <div className="px-6 pb-4">
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, i) => (
                  <Badge
                    key={i}
                    variant="outline"
                    className="cursor-pointer hover:bg-muted transition-smooth"
                    onClick={() => handleSuggestion(suggestion)}
                  >
                    <Sparkles className="h-3 w-3 mr-1" />
                    {suggestion}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-6 border-t">
            <div className="flex gap-4">
              <Textarea
                placeholder="Ask me anything about your career... (max 500 characters)"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value.slice(0, 500))}
                onKeyPress={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="min-h-[60px] max-h-[120px] resize-none"
              />
              <Button
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                className="gradient-primary px-8"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {inputValue.length}/500 characters • Press Enter to send, Shift + Enter for new line
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
