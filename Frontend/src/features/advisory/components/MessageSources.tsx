import { useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Citation } from "@/lib/api";

interface MessageSourcesProps {
  sources: Citation[];
}

const TIER_VARIANT: Record<Citation["confidence_tier"], "default" | "secondary" | "outline"> = {
  HIGH: "default",
  MEDIUM: "secondary",
  LOW: "outline",
};

/**
 * Collapsible "Sources" block rendered under a grounded assistant message.
 *
 * Each source shows its label, a short excerpt, a confidence badge, and — when
 * the licensed corpus provides one — an external link. Renders nothing when the
 * message has no retrieved sources (e.g. scope redirects), so the no-context
 * state is handled separately by the page.
 */
export function MessageSources({ sources }: MessageSourcesProps) {
  const [open, setOpen] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-border/50 pt-2">
      <button
        aria-expanded={open}
        className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        Sources ({sources.length})
      </button>

      {open ? (
        <ul className="mt-2 space-y-2">
          {sources.map((source, index) => (
            <li
              className="rounded-lg bg-background/60 p-2 text-xs"
              key={`${source.source}-${source.section}-${index}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold">
                  {source.source}
                  {source.section ? <span className="text-muted-foreground"> · {source.section}</span> : null}
                </span>
                <Badge className={cn("shrink-0")} variant={TIER_VARIANT[source.confidence_tier] ?? "outline"}>
                  {source.confidence_tier}
                </Badge>
              </div>
              {source.excerpt ? (
                <p className="mt-1 leading-5 text-muted-foreground">{source.excerpt}</p>
              ) : null}
              {source.url ? (
                <a
                  className="mt-1 inline-flex items-center gap-1 text-primary hover:underline"
                  href={source.url}
                  rel="noreferrer"
                  target="_blank"
                >
                  <ExternalLink className="h-3 w-3" />
                  View source
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export default MessageSources;
