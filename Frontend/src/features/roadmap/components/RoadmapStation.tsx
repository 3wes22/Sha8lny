import type { ReactNode } from "react";
import { Check, ChevronDown, Lock, Play } from "lucide-react";

import type { RoadmapMilestone, RoadmapPhase } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { StationState } from "@/features/roadmap/lib/stationState";
import { RoadmapMilestoneRow } from "@/features/roadmap/components/RoadmapMilestoneRow";

interface RoadmapStationProps {
  phase: RoadmapPhase;
  index: number;
  state: StationState;
  expanded: boolean;
  isLast?: boolean;
  updating?: boolean;
  onToggleExpand: () => void;
  onMilestoneToggle: (milestone: RoadmapMilestone) => void;
  children?: ReactNode;
}

const statusMeta: Record<StationState, string> = {
  completed: "Completed",
  current: "In progress",
  next: "Up next",
  locked: "Locked",
};

function Pin({ state, index }: { state: StationState; index: number }) {
  const base =
    "relative z-10 flex h-9 w-9 flex-none items-center justify-center rounded-full text-sm font-semibold shadow-sm";

  if (state === "completed") {
    return (
      <span className={cn(base, "bg-success text-success-foreground")}>
        <Check className="h-4 w-4" />
      </span>
    );
  }
  if (state === "current") {
    return (
      <span className={cn(base, "bg-primary text-primary-foreground ring-4 ring-primary/20")}>
        <Play className="h-4 w-4" />
      </span>
    );
  }
  if (state === "locked") {
    return (
      <span className={cn(base, "border border-border bg-muted text-muted-foreground")}>
        <Lock className="h-3.5 w-3.5" />
      </span>
    );
  }
  return (
    <span className={cn(base, "border border-primary/40 bg-card text-primary")}>{index + 1}</span>
  );
}

export function RoadmapStation({
  phase,
  index,
  state,
  expanded,
  isLast,
  updating,
  onToggleExpand,
  onMilestoneToggle,
  children,
}: RoadmapStationProps) {
  const locked = state === "locked";
  const milestones = phase.milestones ?? [];
  const completion = Number(phase.completion_percentage ?? 0);

  return (
    <div className={cn("relative flex gap-4 pb-4", isLast && "pb-0")}>
      <Pin index={index} state={state} />

      <div
        className={cn(
          "transition-smooth interactive-scale flex-1 rounded-[1.5rem] border bg-card/95 [--interactive-hover-scale:1.004]",
          state === "current" && "border-primary/50 shadow-soft-lg",
          state === "completed" && "border-border/60 opacity-80",
          state === "next" && "border-border/70",
          locked && "border-dashed border-border/70 opacity-60",
          updating && "opacity-60",
        )}
      >
        <button
          aria-expanded={expanded}
          className={cn(
            "flex w-full items-center gap-3 px-5 py-4 text-left",
            locked ? "cursor-not-allowed" : "cursor-pointer",
          )}
          disabled={locked}
          onClick={onToggleExpand}
          type="button"
        >
          <div className="min-w-0 flex-1">
            <p className="type-kicker">
              Phase {phase.order ?? index + 1} · {statusMeta[state]}
            </p>
            <h3 className="mt-1 truncate text-xl font-bold">{phase.title}</h3>
            {state === "current" ? (
              <p className="mt-1 text-sm text-muted-foreground">
                {completion.toFixed(0)}% complete · {phase.estimated_duration_weeks} weeks
              </p>
            ) : null}
          </div>
          {!locked ? (
            <ChevronDown
              className={cn(
                "h-5 w-5 flex-none text-muted-foreground transition-transform",
                expanded && "rotate-180",
              )}
            />
          ) : null}
        </button>

        {!locked && expanded ? (
          <div className="border-t border-border/60 px-5 pb-5 pt-1">
            {phase.description ? (
              <p className="py-3 text-sm leading-6 text-muted-foreground">{phase.description}</p>
            ) : null}
            {milestones.length > 0 ? (
              <div className="relative ml-1 space-y-2 border-l-2 border-dashed border-primary/30 pl-6">
                {milestones.map((milestone) => (
                  <div className="relative" key={milestone.id}>
                    <span
                      aria-hidden="true"
                      className="absolute -left-6 top-1/2 h-px w-5 -translate-y-1/2 bg-primary/30"
                    />
                    <RoadmapMilestoneRow
                      disabled={updating}
                      milestone={milestone}
                      onToggle={onMilestoneToggle}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-3 text-sm text-muted-foreground">No milestones in this phase yet.</p>
            )}
            {children}
          </div>
        ) : null}
      </div>
    </div>
  );
}
