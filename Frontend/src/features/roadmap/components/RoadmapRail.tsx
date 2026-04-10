import type { RoadmapJourneySummary, RoadmapPhase } from "@/lib/api";
import { cn } from "@/lib/utils";

interface RoadmapRailProps {
  phases: RoadmapPhase[];
  currentFocusNodeId?: string;
  summary?: RoadmapJourneySummary;
}

export function RoadmapRail({ phases, currentFocusNodeId, summary }: RoadmapRailProps) {
  return (
    <div className="atlas-panel p-5">
      <p className="type-kicker">Journey rail</p>
      <div className="mt-4 space-y-4">
        {phases.map((phase, index) => {
          const isCurrent =
            currentFocusNodeId === phase.id ||
            phase.milestones?.some((milestone) => milestone.id === currentFocusNodeId);

          return (
            <div className="grid grid-cols-[28px_minmax(0,1fr)] gap-3" key={phase.id}>
              <div className="flex flex-col items-center">
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold",
                    isCurrent ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background",
                  )}
                >
                  {index + 1}
                </span>
                {index < phases.length - 1 ? <span className="atlas-rule mt-2 h-full" /> : null}
              </div>
              <div className={cn("rounded-[1.25rem] p-3", isCurrent && "bg-primary/5")}>
                <p className="text-sm font-semibold">{phase.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {phase.completed_milestones ?? 0}/{phase.total_milestones ?? phase.milestones?.length ?? 0} milestones complete
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {summary ? (
        <div className="mt-5 rounded-[1.5rem] bg-foreground px-4 py-5 text-background">
          <p className="type-kicker text-background/60">{summary.focus_label}</p>
          <p className="mt-2 text-xl font-bold">{summary.next_action_title}</p>
          <p className="mt-2 text-sm leading-6 text-background/70">{summary.next_action_summary}</p>
        </div>
      ) : null}
    </div>
  );
}
