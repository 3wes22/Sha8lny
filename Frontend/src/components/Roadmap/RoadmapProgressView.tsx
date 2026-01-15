import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Circle,
  Clock,
  Trophy,
  BookOpen,
  Code,
  FileText,
  Target,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { Roadmap, RoadmapPhase, RoadmapMilestone } from "@/lib/api";
import { roadmapApi } from "@/lib/api";
import { toast } from "sonner";

interface RoadmapProgressViewProps {
  roadmap: Roadmap;
  onProgressUpdate?: () => void;
}

const getMilestoneIcon = (type: string) => {
  switch (type) {
    case "course":
      return BookOpen;
    case "project":
      return Code;
    case "reading":
      return FileText;
    case "practice":
      return Target;
    case "assessment":
      return Trophy;
    default:
      return Circle;
  }
};

const getMilestoneColor = (type: string) => {
  switch (type) {
    case "course":
      return "text-blue-600 bg-blue-500/10";
    case "project":
      return "text-purple-600 bg-purple-500/10";
    case "reading":
      return "text-emerald-600 bg-emerald-500/10";
    case "practice":
      return "text-amber-600 bg-amber-500/10";
    case "assessment":
      return "text-rose-600 bg-rose-500/10";
    default:
      return "text-gray-600 bg-gray-500/10";
  }
};

const PhaseCard: React.FC<{
  phase: RoadmapPhase;
  roadmapId: string;
  phaseNumber: number;
  onProgressUpdate?: () => void;
}> = ({ phase, roadmapId, phaseNumber, onProgressUpdate }) => {
  const [expanded, setExpanded] = useState(phase.status === "in_progress");
  const [updating, setUpdating] = useState(false);

  const completedCount = phase.milestones?.filter((m) => m.status === "completed").length || 0;
  const totalCount = phase.milestones?.length || 0;
  const progressPercent = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  const handleMilestoneToggle = async (milestone: RoadmapMilestone) => {
    try {
      setUpdating(true);

      const newStatus = milestone.status === "completed" ? "not_started" : "completed";

      await roadmapApi.updateProgress(roadmapId, {
        milestone_id: milestone.id,
        status: newStatus,
      });

      toast.success(
        newStatus === "completed"
          ? `Milestone completed! 🎉`
          : "Milestone marked as not started"
      );

      onProgressUpdate?.();
    } catch (error: any) {
      console.error("Error updating milestone:", error);
      toast.error(error?.response?.data?.message || "Failed to update milestone");
    } finally {
      setUpdating(false);
    }
  };

  return (
    <Card className="border-subtle shadow-soft-lg overflow-hidden">
      <CardHeader
        className="cursor-pointer hover:bg-muted/50 transition-smooth pb-4"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                Phase {phaseNumber}
              </Badge>
              <Badge
                variant={phase.status === "completed" ? "default" : "outline"}
                className={`text-xs capitalize ${
                  phase.status === "completed"
                    ? "bg-green-500/10 text-green-600 border-green-500/20"
                    : phase.status === "in_progress"
                    ? "bg-primary/10 text-primary border-primary/20"
                    : ""
                }`}
              >
                {phase.status.replace("_", " ")}
              </Badge>
            </div>

            <CardTitle className="text-base md:text-lg font-semibold flex items-center gap-2">
              {phase.status === "completed" ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground" />
              )}
              {phase.title}
            </CardTitle>

            <p className="text-xs md:text-sm text-muted-foreground">{phase.description}</p>

            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {phase.estimated_duration_weeks} weeks
              </span>
              <span>
                {completedCount} of {totalCount} milestones completed
              </span>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary to-cyan-400 transition-all duration-700"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          <Button variant="ghost" size="sm" className="shrink-0">
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-3 pt-0">
          {/* Objectives */}
          {phase.objectives && phase.objectives.length > 0 && (
            <div className="rounded-xl bg-muted/30 p-3 space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Learning Objectives
              </div>
              <ul className="space-y-1">
                {phase.objectives.map((objective, idx) => (
                  <li key={idx} className="text-xs text-foreground flex items-start gap-2">
                    <Target className="h-3.5 w-3.5 mt-0.5 text-primary shrink-0" />
                    {objective}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Milestones */}
          <div className="space-y-2">
            {phase.milestones?.map((milestone, idx) => {
              const Icon = getMilestoneIcon(milestone.milestone_type);
              const colorClass = getMilestoneColor(milestone.milestone_type);
              const isCompleted = milestone.status === "completed";

              return (
                <button
                  key={milestone.id}
                  onClick={() => handleMilestoneToggle(milestone)}
                  disabled={updating}
                  className={[
                    "w-full rounded-xl border p-3 text-left transition-smooth",
                    "hover:shadow-md hover:-translate-y-0.5",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    isCompleted
                      ? "bg-green-50 border-green-200 dark:bg-green-500/5 dark:border-green-500/20"
                      : "bg-card border-subtle hover:bg-muted/50",
                  ].join(" ")}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`inline-flex h-8 w-8 items-center justify-center rounded-lg shrink-0 ${colorClass}`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-sm font-semibold ${
                            isCompleted ? "line-through text-muted-foreground" : ""
                          }`}
                        >
                          {milestone.title}
                        </span>
                        {milestone.is_required && (
                          <Badge variant="outline" className="text-[10px]">
                            Required
                          </Badge>
                        )}
                      </div>

                      <p className="text-xs text-muted-foreground">{milestone.description}</p>

                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {milestone.estimated_duration_hours}h
                        </span>
                        <span className="capitalize">{milestone.milestone_type}</span>
                        {milestone.skills && milestone.skills.length > 0 && (
                          <span className="hidden sm:inline">
                            Skills: {milestone.skills.join(", ")}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="shrink-0">
                      {isCompleted ? (
                        <CheckCircle2 className="h-6 w-6 text-green-600" />
                      ) : (
                        <Circle className="h-6 w-6 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export const RoadmapProgressView: React.FC<RoadmapProgressViewProps> = ({
  roadmap,
  onProgressUpdate,
}) => {
  if (!roadmap.phases || roadmap.phases.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-subtle bg-muted/30 p-8 text-center">
        <div className="mx-auto max-w-md space-y-3">
          <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <BookOpen className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No Phases Yet</h3>
          <p className="text-sm text-muted-foreground">
            This roadmap doesn't have any learning phases yet. Phases and milestones will be
            generated when you create a roadmap from a template.
          </p>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight">Your Learning Path</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Track your progress through each phase and milestone
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {roadmap.completed_phases || 0} / {roadmap.total_phases || 0} phases
          </Badge>
        </div>
      </div>

      <div className="space-y-4">
        {roadmap.phases.map((phase, idx) => (
          <PhaseCard
            key={phase.id}
            phase={phase}
            roadmapId={roadmap.id}
            phaseNumber={idx + 1}
            onProgressUpdate={onProgressUpdate}
          />
        ))}
      </div>
    </section>
  );
};
