import React, { useState } from "react";

import { StatePanel } from "@/shared/components/StatePanel";
import { getApiErrorMessage, roadmapApi, type Roadmap, type RoadmapMilestone } from "@/lib/api";
import { RoadmapAtlas } from "@/features/roadmap/components/RoadmapAtlas";
import { RoadmapRail } from "@/features/roadmap/components/RoadmapRail";
import { toast } from "sonner";

interface RoadmapProgressViewProps {
  roadmap: Roadmap;
  onProgressUpdate?: () => void;
}

export const RoadmapProgressView: React.FC<RoadmapProgressViewProps> = ({
  roadmap,
  onProgressUpdate,
}) => {
  const [updating, setUpdating] = useState(false);

  const handleMilestoneToggle = async (milestone: RoadmapMilestone) => {
    try {
      setUpdating(true);
      await roadmapApi.updateProgress(roadmap.id, {
        milestone_id: milestone.id,
        status: milestone.status === "completed" ? "not_started" : "completed",
      });
      toast.success(
        milestone.status === "completed"
          ? "Milestone returned to the queue."
          : "Milestone marked complete.",
      );
      onProgressUpdate?.();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update milestone"));
    } finally {
      setUpdating(false);
    }
  };

  if (!roadmap.phases || roadmap.phases.length === 0) {
    return (
      <StatePanel
        description="This roadmap does not include phases yet. Generate a roadmap from a template to see the atlas."
        state="empty"
        title="No phases yet"
      />
    );
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className={updating ? "opacity-75 transition-smooth" : ""}>
        <RoadmapAtlas onMilestoneToggle={handleMilestoneToggle} roadmap={roadmap} />
      </div>
      <RoadmapRail
        currentFocusNodeId={roadmap.current_focus_node_id}
        phases={roadmap.phases}
        summary={roadmap.journey_summary}
      />
    </div>
  );
};
