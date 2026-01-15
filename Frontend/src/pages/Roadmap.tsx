import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Map, Loader2 } from "lucide-react";
import { RoadmapProgressView } from "@/components/Roadmap/RoadmapProgressView";
import { roadmapTemplateApi, roadmapApi, type RoadmapTemplate, type Roadmap as RoadmapType } from "@/lib/api";
import { toast } from "sonner";

const RoadmapPage: React.FC = () => {
  const [templates, setTemplates] = useState<RoadmapTemplate[]>([]);
  const [activeRoadmap, setActiveRoadmap] = useState<RoadmapType | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch templates and active roadmap in parallel
      const [templatesRes, roadmapsRes] = await Promise.all([
        roadmapTemplateApi.list(),
        roadmapApi.list({ status: 'active' })
      ]);

      setTemplates(templatesRes.results || []);

      // Get the first active roadmap if any
      const activeRoadmaps = roadmapsRes.results || [];
      if (activeRoadmaps.length > 0) {
        // Fetch full roadmap details with hierarchy
        const fullRoadmap = await roadmapApi.get(activeRoadmaps[0].id);
        setActiveRoadmap(fullRoadmap);
      }
    } catch (error: any) {
      console.error('Error fetching roadmap data:', error);
      toast.error(error?.response?.data?.message || 'Failed to load roadmap data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoadmap = async (templateId: string) => {
    try {
      setCreating(true);

      const roadmap = await roadmapApi.createFromTemplate({
        template_id: templateId,
        weekly_hours_commitment: 15
      });

      toast.success('Roadmap created successfully!');

      // Fetch full roadmap details
      const fullRoadmap = await roadmapApi.get(roadmap.id);
      setActiveRoadmap(fullRoadmap);
    } catch (error: any) {
      console.error('Error creating roadmap:', error);
      toast.error(error?.response?.data?.message || 'Failed to create roadmap');
    } finally {
      setCreating(false);
    }
  };

  const handleActivateRoadmap = async () => {
    if (!activeRoadmap) return;

    try {
      const updatedRoadmap = await roadmapApi.activate(activeRoadmap.id);
      setActiveRoadmap(updatedRoadmap);
      toast.success('Roadmap activated! Start learning now.');
    } catch (error: any) {
      console.error('Error activating roadmap:', error);
      toast.error(error?.response?.data?.message || 'Failed to activate roadmap');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Extract top 3 templates as recommended (sorted by usage_count)
  const recommendedTemplates = templates.slice(0, 3);

  return (
    <div className="space-y-8">
      {/* Hero / header */}
      <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Career Roadmap
          </h1>
          <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
            A step-by-step learning plan to grow in your chosen career path.
            Track your progress and deep-dive into each track to see exactly what to learn next.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="text-xs md:text-sm">
            View Learning Pace
          </Button>
          <Button size="sm" className="text-xs md:text-sm gradient-primary">
            <Map className="mr-2 h-4 w-4" />
            Download Roadmap
          </Button>
        </div>
      </section>

      {/* Active Roadmap Overview or Create Roadmap */}
      {activeRoadmap ? (
        <section className="space-y-5">
          <div className="relative overflow-hidden rounded-2xl border border-subtle shadow-soft-lg">
            {/* soft glow */}
            <div className="pointer-events-none absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-cyan-500/15 blur-3xl" />

            <div className="gradient-soft px-5 py-5 md:px-7 md:py-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <Map className="h-4 w-4" />
                    </span>
                    <h2 className="text-base md:text-lg font-semibold">
                      {activeRoadmap.title}
                    </h2>
                  </div>
                  <p className="text-xs md:text-sm text-muted-foreground max-w-2xl">
                    {activeRoadmap.description}
                  </p>
                </div>

                {/* Stats pills */}
                <div className="flex flex-wrap gap-2">
                  <div className="rounded-full border border-subtle bg-card px-3 py-1.5 text-xs">
                    <span className="text-muted-foreground">Phases:</span>{" "}
                    <span className="font-semibold text-foreground">
                      {activeRoadmap.total_phases || 0}
                    </span>
                  </div>
                  <div className="rounded-full border border-subtle bg-card px-3 py-1.5 text-xs">
                    <span className="text-muted-foreground">Status:</span>{" "}
                    <span className="font-semibold text-foreground capitalize">
                      {activeRoadmap.status}
                    </span>
                  </div>
                  <div className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs text-primary">
                    Personalized learning
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-5 space-y-2">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Roadmap completion</span>
                  <span className="font-medium text-foreground">
                    {parseFloat(activeRoadmap.completion_percentage).toFixed(0)}%
                  </span>
                </div>

                <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary via-indigo-500 to-cyan-400 transition-all duration-700"
                    style={{ width: `${activeRoadmap.completion_percentage}%` }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground">
                    {activeRoadmap.completed_phases || 0} of {activeRoadmap.total_phases || 0} phases completed
                  </div>
                  {activeRoadmap.status === 'draft' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleActivateRoadmap}
                      className="text-xs"
                    >
                      Activate Roadmap
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="space-y-5">
          <div className="rounded-2xl border border-dashed border-subtle bg-muted/30 p-8 text-center">
            <div className="mx-auto max-w-md space-y-3">
              <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Map className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold">No Active Roadmap</h3>
              <p className="text-sm text-muted-foreground">
                Choose a career track below to create your personalized learning roadmap.
                We'll generate a step-by-step plan based on your goals.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Roadmap Templates */}
      <div className="rounded-2xl border border-subtle bg-card p-4 shadow-soft-lg">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold">
              {activeRoadmap ? 'Other Career Tracks' : 'Choose Your Career Track'}
            </h3>
            <p className="text-xs text-muted-foreground">
              {templates.length} roadmap templates available. Click to create your personalized plan.
            </p>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-xs">
              Filter by Level
            </Button>
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {templates.map((template) => {
            const isRecommended = recommendedTemplates.some(t => t.id === template.id);

            return (
              <button
                key={template.id}
                onClick={() => handleCreateRoadmap(template.id)}
                disabled={creating}
                className={[
                  "rounded-2xl border p-3 text-left transition-smooth",
                  "hover:-translate-y-0.5 hover:shadow-md",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  isRecommended
                    ? "border-primary/30 bg-primary/5 ring-1 ring-primary/20"
                    : "border-subtle bg-card hover:bg-muted/60",
                ].join(" ")}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="text-sm font-semibold">{template.target_career}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      {template.estimated_duration_weeks} weeks • {template.difficulty_level}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                      {template.usage_count} users following
                    </div>
                  </div>

                  {isRecommended && (
                    <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[10px] text-primary shrink-0">
                      Popular
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {creating && (
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Creating your personalized roadmap...</span>
          </div>
        )}
      </div>

      {/* Roadmap Progress Tracker - Only show if active roadmap exists */}
      {activeRoadmap && (
        <RoadmapProgressView
          roadmap={activeRoadmap}
          onProgressUpdate={fetchData}
        />
      )}
    </div>
  );
};

export default RoadmapPage;
