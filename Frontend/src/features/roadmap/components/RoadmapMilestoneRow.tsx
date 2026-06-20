import { Check, Clock3 } from "lucide-react";

import type { RoadmapMilestone } from "@/lib/api";
import { cn } from "@/lib/utils";

interface RoadmapMilestoneRowProps {
  milestone: RoadmapMilestone;
  onToggle: (milestone: RoadmapMilestone) => void;
  disabled?: boolean;
}

const typePillClass: Record<RoadmapMilestone["milestone_type"], string> = {
  course: "bg-accent/10 text-accent-foreground/90 border-accent/30",
  project: "bg-primary/10 text-primary border-primary/30",
  reading: "bg-info/10 text-info border-info/30",
  practice: "bg-warning/10 text-warning border-warning/40",
  assessment: "bg-success/10 text-success border-success/30",
};

export function RoadmapMilestoneRow({ milestone, onToggle, disabled }: RoadmapMilestoneRowProps) {
  const isComplete = milestone.status === "completed";
  const fromAssessment = isComplete && milestone.completed_from_assessment === true;

  return (
    <button
      aria-checked={isComplete}
      className={cn(
        "transition-smooth group flex w-full items-center gap-3 rounded-xl border border-border/60 bg-background/60 px-3 py-2.5 text-left",
        disabled ? "cursor-not-allowed opacity-60" : "hover:border-primary/40 hover:text-foreground",
      )}
      disabled={disabled}
      onClick={() => onToggle(milestone)}
      role="checkbox"
      type="button"
    >
      <span
        aria-hidden="true"
        className={cn(
          "transition-smooth flex h-5 w-5 flex-none items-center justify-center rounded-md border-2",
          isComplete ? "border-success bg-success text-success-foreground" : "border-border group-hover:border-primary",
        )}
      >
        {isComplete ? <Check className="h-3 w-3" /> : null}
      </span>

      <span className="flex min-w-0 flex-1 flex-col">
        <span className={cn("min-w-0 text-sm", isComplete && "text-muted-foreground line-through")}>
          {milestone.title}
        </span>
        {fromAssessment ? (
          <span className="text-[0.7rem] font-medium text-muted-foreground no-underline">
            Marked from your assessment ·{" "}
            <span className="text-primary underline-offset-2 group-hover:underline">Revise</span>
          </span>
        ) : null}
      </span>

      <span
        className={cn(
          "hidden flex-none rounded-full border px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide sm:inline-block",
          typePillClass[milestone.milestone_type] ?? "bg-muted/50 text-muted-foreground border-border/60",
        )}
      >
        {milestone.milestone_type}
      </span>

      <span className="flex flex-none items-center gap-1 text-xs text-muted-foreground">
        <Clock3 className="h-3.5 w-3.5" />
        {milestone.estimated_duration_hours}h
      </span>
    </button>
  );
}
