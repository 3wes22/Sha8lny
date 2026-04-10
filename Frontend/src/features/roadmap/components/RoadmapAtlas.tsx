import type { Roadmap, RoadmapMilestone, RoadmapPhase } from "@/lib/api";

import { RoadmapNodeCard } from "@/features/roadmap/components/RoadmapNodeCard";

interface RoadmapAtlasProps {
  roadmap: Roadmap;
  onMilestoneToggle: (milestone: RoadmapMilestone) => void;
}

const toNodeStatus = (status: RoadmapPhase["status"] | RoadmapMilestone["status"]) => {
  if (status === "completed") return "completed";
  if (status === "in_progress") return "active";
  if (status === "not_started") return "available";
  return "locked";
};

export function RoadmapAtlas({ roadmap, onMilestoneToggle }: RoadmapAtlasProps) {
  return (
    <div className="space-y-6">
      {roadmap.phases?.map((phase, phaseIndex) => (
        <section className="atlas-panel overflow-hidden" key={phase.id}>
          <div className="border-b border-border/70 px-5 py-4 md:px-6">
            <p className="type-kicker">Phase {phaseIndex + 1}</p>
            <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <h3 className="text-2xl font-bold">{phase.title}</h3>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                  {phase.description}
                </p>
              </div>
              <div className="text-right text-sm text-muted-foreground">
                <p>{Number(phase.completion_percentage ?? 0).toFixed(0)}% complete</p>
                <p>{phase.estimated_duration_weeks} weeks</p>
              </div>
            </div>
          </div>

          <div className="grid gap-4 px-5 py-5 md:px-6 lg:grid-cols-2">
            {phase.milestones?.map((milestone) => (
              <RoadmapNodeCard
                actionLabel={milestone.status === "completed" ? "Mark as pending" : "Mark complete"}
                description={milestone.description}
                detail={`${milestone.estimated_duration_hours} hours`}
                key={milestone.id}
                meta={milestone.milestone_type.replaceAll("_", " ")}
                onAction={() => onMilestoneToggle(milestone)}
                status={toNodeStatus(milestone.status)}
                title={milestone.title}
              />
            )) ?? []}
          </div>
        </section>
      ))}
    </div>
  );
}
