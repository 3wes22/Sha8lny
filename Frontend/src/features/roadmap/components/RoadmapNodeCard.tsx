import { CheckCircle2, CircleDot, Clock3, Lock, PlayCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type AtlasNodeStatus = "locked" | "available" | "active" | "completed";

interface RoadmapNodeCardProps {
  title: string;
  description?: string;
  status: AtlasNodeStatus;
  meta?: string;
  detail?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const statusIcon = {
  locked: Lock,
  available: CircleDot,
  active: PlayCircle,
  completed: CheckCircle2,
} as const;

const statusLabel = {
  locked: "Locked",
  available: "Ready",
  active: "In motion",
  completed: "Done",
} as const;

export function RoadmapNodeCard({
  title,
  description,
  status,
  meta,
  detail,
  actionLabel,
  onAction,
}: RoadmapNodeCardProps) {
  const Icon = statusIcon[status];

  return (
    <div
      className={cn(
        "panel-paper rounded-[1.5rem] p-4",
        status === "active" && "border-primary/30 bg-primary/5",
        status === "completed" && "border-success/25 bg-success/10",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline">{statusLabel[status]}</Badge>
            {meta ? <span className="text-xs text-muted-foreground">{meta}</span> : null}
          </div>
          <h4 className="text-lg font-semibold">{title}</h4>
          {description ? <p className="text-sm leading-6 text-muted-foreground">{description}</p> : null}
        </div>
        <div className="rounded-2xl bg-background/80 p-3">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>

      {detail ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
          <Clock3 className="h-4 w-4" />
          <span>{detail}</span>
        </div>
      ) : null}

      {actionLabel && onAction ? (
        <Button className="mt-4 w-full" onClick={onAction} variant={status === "completed" ? "outline" : "default"}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
