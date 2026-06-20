import { useState } from "react";

import type { Roadmap, RoadmapMilestone } from "@/lib/api";
import { StatePanel } from "@/shared/components/StatePanel";
import {
  deriveStationState,
  getCurrentPhaseIndex,
} from "@/features/roadmap/lib/stationState";
import { RoadmapStation } from "@/features/roadmap/components/RoadmapStation";
import { RoadmapSourcesPanel } from "@/features/roadmap/components/RoadmapSourcesPanel";

interface RoadmapTrailProps {
  roadmap: Roadmap;
  onMilestoneToggle: (milestone: RoadmapMilestone) => void;
  updating?: boolean;
}

export function RoadmapTrail({ roadmap, onMilestoneToggle, updating }: RoadmapTrailProps) {
  const phases = roadmap.phases ?? [];
  const currentIndex = getCurrentPhaseIndex(phases);
  const currentPhaseId = currentIndex >= 0 ? phases[currentIndex]?.id : phases[0]?.id;
  const [expandedId, setExpandedId] = useState<string | null>(currentPhaseId ?? null);

  if (phases.length === 0) {
    return (
      <StatePanel
        description="This roadmap does not include phases yet. Generate a roadmap from a template to draw the trail."
        state="empty"
        title="No phases yet"
      />
    );
  }

  const completedCount = phases.filter(
    (phase) => phase.status === "completed" || phase.status === "skipped",
  ).length;
  const greenStop = (completedCount / phases.length) * 100;
  const orangeStop = Math.min(greenStop + 100 / phases.length, 100);

  return (
    <div className="relative pl-1">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-6 left-[1.4rem] top-4 w-[3px] rounded-full"
        style={{
          backgroundImage: `linear-gradient(to bottom, hsl(var(--success)) 0%, hsl(var(--success)) ${greenStop}%, hsl(var(--primary)) ${greenStop}%, hsl(var(--primary)) ${orangeStop}%, hsl(var(--border)) ${orangeStop}%, hsl(var(--border)) 100%)`,
        }}
      />

      <div className="space-y-0">
        {phases.map((phase, index) => {
          const state = deriveStationState(phase, index, phases);

          return (
            <RoadmapStation
              expanded={expandedId === phase.id}
              index={index}
              isLast={index === phases.length - 1}
              key={phase.id}
              onMilestoneToggle={onMilestoneToggle}
              onToggleExpand={() =>
                setExpandedId((current) => (current === phase.id ? null : phase.id))
              }
              phase={phase}
              state={state}
              updating={updating}
            >
              {state === "current" ? (
                <div className="mt-3">
                  <RoadmapSourcesPanel roadmap={roadmap} />
                </div>
              ) : null}
            </RoadmapStation>
          );
        })}
      </div>
    </div>
  );
}
