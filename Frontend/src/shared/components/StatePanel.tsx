import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type StateKind = "loading" | "processing" | "error" | "empty" | "success";

const stateIcons = {
  loading: Loader2,
  processing: Clock3,
  error: AlertTriangle,
  empty: Sparkles,
  success: CheckCircle2,
} as const;

const stateClasses: Record<StateKind, string> = {
  loading: "border-border/70 bg-card/90",
  processing: "border-primary/20 bg-primary/5",
  error: "border-destructive/25 bg-destructive/5",
  empty: "border-border/70 bg-muted/45",
  success: "border-success/25 bg-success/10",
};

interface StatePanelProps {
  state: StateKind;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  action?: ReactNode;
  className?: string;
}

export function StatePanel({
  state,
  title,
  description,
  actionLabel,
  onAction,
  action,
  className,
}: StatePanelProps) {
  const Icon = stateIcons[state];

  return (
    <div className={cn("atlas-panel p-6", stateClasses[state], className)}>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-background/80 p-3">
            <Icon className={cn("h-5 w-5", state === "loading" && "animate-spin")} />
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-semibold">{title}</h3>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">{description}</p>
          </div>
        </div>
        {action ?? (actionLabel && onAction ? <Button onClick={onAction}>{actionLabel}</Button> : null)}
      </div>
    </div>
  );
}
