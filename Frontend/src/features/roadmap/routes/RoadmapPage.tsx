import React, { useCallback, useEffect, useState } from "react";
import { Loader2, Map, Sparkles } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { ChoiceCard } from "@/shared/components/ChoiceCard";
import { PageShell } from "@/shared/components/PageShell";
import { SectionHeader } from "@/shared/components/SectionHeader";
import { StatePanel } from "@/shared/components/StatePanel";
import { getApiErrorMessage } from "@/lib/api";
import { RoadmapProgressView } from "@/features/roadmap/components/RoadmapProgressView";
import { roadmapTemplateApi, roadmapApi, type RoadmapTemplate, type Roadmap as RoadmapType } from "@/lib/api";
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

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const recommendedTemplates = templates.slice(0, 3);
  const roadmapGenerating = !!activeRoadmap && ["pending", "processing"].includes(activeRoadmap.ai_processing_status);

  return (
    <PageShell
      actions={
        <Button className="gradient-primary">
          <Map className="mr-2 h-4 w-4" />
          {activeRoadmap
            ? roadmapGenerating
              ? "Generating atlas"
              : activeRoadmap.status === "draft"
              ? "Draft ready"
              : "Atlas active"
            : "Choose a direction"}
        </Button>
      }
      description="The roadmap view should feel like a navigable learning atlas, not a pile of unrelated progress widgets."
      eyebrow="Roadmap"
      title="Career roadmap"
    >
      {activeRoadmap ? (
        <div className="atlas-panel p-6">
          <p className="type-kicker">Current roadmap</p>
          <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-3xl font-bold">{activeRoadmap.title}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                {activeRoadmap.description}
              </p>
            </div>
            {activeRoadmap.status === "draft" ? (
              <Button onClick={handleActivateRoadmap} variant="outline">
                Activate roadmap
              </Button>
            ) : null}
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Completion</p>
              <p className="mt-2 text-2xl font-bold">
                {Number(activeRoadmap.completion_percentage).toFixed(0)}%
              </p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Current focus</p>
              <p className="mt-2 text-2xl font-bold">
                {activeRoadmap.journey_summary?.next_action_title ?? "Pending"}
              </p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Structure</p>
              <p className="mt-2 text-2xl font-bold">{activeRoadmap.total_phases ?? 0} phases</p>
            </div>
          </div>
        </div>
      ) : (
        <StatePanel
          description="Choose a roadmap template to generate an atlas-style learning path you can actually follow."
          state="empty"
          title="No active roadmap yet"
        />
      )}

      <section className="space-y-4">
        <SectionHeader
          description="Templates stay visible even when a roadmap exists so users can compare direction and switch tracks deliberately."
          title={activeRoadmap ? "Other tracks" : "Choose your track"}
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {templates.map((template) => {
            const isRecommended = recommendedTemplates.some((recommended) => recommended.id === template.id);

            return (
              <ChoiceCard
                description={template.short_description || template.description}
                disabled={creating}
                icon={<Sparkles className="h-5 w-5 text-primary" />}
                key={template.id}
                meta={`${template.estimated_duration_weeks} weeks • ${template.difficulty_level}${isRecommended ? " • popular" : ""}`}
                onClick={() => handleCreateRoadmap(template.id)}
                selected={activeRoadmap?.template === template.id}
                title={template.target_career}
              />
            );
          })}
        </div>

        {creating || roadmapGenerating ? (
          <StatePanel
            description="We are generating the roadmap structure and preparing the first phase."
            state="processing"
            title="Creating roadmap"
          />
        ) : null}
      </section>

      {activeRoadmap && !roadmapGenerating ? (
        <RoadmapProgressView
          onProgressUpdate={fetchData}
          roadmap={activeRoadmap}
        />
      ) : null}
    </PageShell>
  );
};

export default RoadmapPage;
