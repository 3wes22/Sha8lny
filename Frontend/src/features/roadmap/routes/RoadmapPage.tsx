import React, { useCallback, useEffect, useState } from "react";
import { ChevronDown, Loader2, Map, Sparkles } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { ChoiceCard } from "@/shared/components/ChoiceCard";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { getApiErrorMessage } from "@/lib/api";
import { RoadmapTrail } from "@/features/roadmap/components/RoadmapTrail";
import {
  roadmapTemplateApi,
  roadmapApi,
  type RoadmapMilestone,
  type RoadmapTemplate,
  type Roadmap as RoadmapType,
} from "@/lib/api";
import { toast } from "sonner";

const CURRENT_ROADMAP_STATUSES = ["in_progress", "active", "draft"] as const;

const RoadmapPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  // A just-created roadmap (e.g. from the assessment results page) passes its
  // id here so we display THAT roadmap rather than resolving to a pre-existing
  // active one — otherwise a freshly generated draft is shadowed and invisible.
  const preferredRoadmapId = (location.state as { roadmapId?: string } | null)?.roadmapId;
  const [templates, setTemplates] = useState<RoadmapTemplate[]>([]);
  const [activeRoadmap, setActiveRoadmap] = useState<RoadmapType | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);

  const loadCurrentRoadmap = useCallback(async () => {
    if (preferredRoadmapId) {
      try {
        return await roadmapApi.get(preferredRoadmapId);
      } catch {
        // Fall back to the status scan if that id is gone.
      }
    }

    for (const status of CURRENT_ROADMAP_STATUSES) {
      const response = await roadmapApi.list({ status });
      const roadmapSummary = response.results[0];

      if (roadmapSummary) {
        return roadmapSummary;
      }
    }

    return null;
  }, [preferredRoadmapId]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [templatesRes, currentRoadmap] = await Promise.all([
        roadmapTemplateApi.list(),
        loadCurrentRoadmap(),
      ]);

      setTemplates(templatesRes.results || []);

      if (currentRoadmap) {
        setActiveRoadmap(await roadmapApi.get(currentRoadmap.id));
      } else {
        setActiveRoadmap(null);
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to load roadmap data"));
    } finally {
      setLoading(false);
    }
  }, [loadCurrentRoadmap]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!activeRoadmap || !["pending", "processing"].includes(activeRoadmap.ai_processing_status)) {
      return;
    }

    const timer = window.setTimeout(() => {
      void fetchData();
    }, 2000);

    return () => window.clearTimeout(timer);
  }, [activeRoadmap, fetchData]);

  const handleCreateRoadmap = async (templateId: string) => {
    try {
      setCreating(true);
      const roadmap = await roadmapApi.createFromTemplate({
        template_id: templateId,
        weekly_hours_commitment: 15,
      });

      toast.success("Roadmap created successfully.");
      setActiveRoadmap(await roadmapApi.get(roadmap.id));
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create roadmap"));
    } finally {
      setCreating(false);
    }
  };

  const handleActivateRoadmap = async () => {
    if (!activeRoadmap) return;

    try {
      setActiveRoadmap(await roadmapApi.activate(activeRoadmap.id));
      toast.success("Roadmap activated.");
      navigate(ROUTES.dashboard);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to activate roadmap"));
    }
  };

  const handleMilestoneToggle = async (milestone: RoadmapMilestone) => {
    if (!activeRoadmap) return;

    try {
      setUpdating(true);
      await roadmapApi.updateProgress(activeRoadmap.id, {
        milestone_id: milestone.id,
        status: milestone.status === "completed" ? "not_started" : "completed",
      });
      toast.success(
        milestone.status === "completed"
          ? "Milestone returned to the queue."
          : "Milestone marked complete.",
      );
      await fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update milestone"));
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const roadmapGenerating =
    !!activeRoadmap && ["pending", "processing"].includes(activeRoadmap.ai_processing_status);
  const completion = activeRoadmap ? Number(activeRoadmap.completion_percentage ?? 0) : 0;
  const focusTitle = activeRoadmap?.journey_summary?.next_action_title;

  const trackPicker = (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {templates.map((template) => (
        <ChoiceCard
          description={template.short_description || template.description}
          disabled={creating}
          icon={<Sparkles className="h-5 w-5 text-primary" />}
          key={template.id}
          meta={`${template.estimated_duration_weeks} weeks • ${template.difficulty_level}`}
          onClick={() => handleCreateRoadmap(template.id)}
          selected={activeRoadmap?.template === template.id}
          title={template.target_career}
        />
      ))}
    </div>
  );

  return (
    <PageShell
      actions={
        <Button className="gradient-primary" disabled>
          <Map className="mr-2 h-4 w-4" />
          {activeRoadmap
            ? roadmapGenerating
              ? "Drawing your route"
              : activeRoadmap.status === "draft"
              ? "Draft ready"
              : `${completion.toFixed(0)}% complete`
            : "Choose a direction"}
        </Button>
      }
      description={
        activeRoadmap
          ? activeRoadmap.description
          : "Pick a direction and we'll draw a personalized trail you can actually follow — one station at a time."
      }
      eyebrow="Roadmap"
      title={activeRoadmap ? activeRoadmap.title : "Career roadmap"}
    >
      {creating || roadmapGenerating ? (
        <StatePanel
          description="We are drawing the trail structure and preparing your first station."
          state="processing"
          title="Creating roadmap"
        />
      ) : null}

      {activeRoadmap && !roadmapGenerating ? (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Journey complete</p>
              <p className="mt-2 text-2xl font-bold">{completion.toFixed(0)}%</p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Current focus</p>
              <p className="mt-2 truncate text-2xl font-bold">{focusTitle ?? "Get started"}</p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Structure</p>
              <p className="mt-2 text-2xl font-bold">{activeRoadmap.total_phases ?? 0} phases</p>
            </div>
          </div>

          {activeRoadmap.status === "draft" ? (
            <div className="flex justify-end">
              <Button onClick={handleActivateRoadmap} variant="outline">
                Activate roadmap
              </Button>
            </div>
          ) : null}

          <RoadmapTrail
            onMilestoneToggle={handleMilestoneToggle}
            roadmap={activeRoadmap}
            updating={updating}
          />
        </>
      ) : !creating ? (
        <StatePanel
          description="Open “Choose your track” below to generate a trail-style learning path tailored to you."
          state="empty"
          title="No active roadmap yet"
        />
      ) : null}

      {!creating && !roadmapGenerating ? (
        <details className="atlas-panel group overflow-hidden" open={!activeRoadmap}>
          <summary className="focus-ring flex cursor-pointer list-none items-center justify-between px-5 py-4">
            <span>
              <span className="type-kicker">{activeRoadmap ? "Switch track" : "Choose your track"}</span>
              <span className="mt-1 block text-sm text-muted-foreground">
                {activeRoadmap
                  ? "Compare other directions and switch deliberately."
                  : "Pick a direction to generate your roadmap."}
              </span>
            </span>
            <ChevronDown className="h-5 w-5 text-muted-foreground transition-transform group-open:rotate-180" />
          </summary>
          <div className="border-t border-border/60 p-5">{trackPicker}</div>
        </details>
      ) : null}
    </PageShell>
  );
};

export default RoadmapPage;
