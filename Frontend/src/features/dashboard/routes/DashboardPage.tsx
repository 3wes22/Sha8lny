import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Compass, Loader2, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { useAuth } from "@/features/auth/context/AuthContext";
import { roadmapApi, type Roadmap, type RoadmapMilestone, type RoadmapPhase, type RoadmapStats } from "@/lib/api";
import { toast } from "sonner";

const getPhaseProgress = (phase: RoadmapPhase | null, roadmap: Roadmap | null) => {
  const phaseProgress = Number(phase?.completion_percentage ?? Number.NaN);

  if (!Number.isNaN(phaseProgress)) {
    return Math.round(phaseProgress);
  }

  return Math.round(Number(roadmap?.completion_percentage ?? 0));
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [stats, setStats] = useState<RoadmapStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const firstName = user?.full_name?.split(" ")[0] || user?.username || "User";

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const inProgress = await roadmapApi.list({ status: "in_progress" });
        const active = inProgress.results.length > 0 ? inProgress : await roadmapApi.list({ status: "active" });
        const activeRoadmap = active.results[0];

        if (activeRoadmap) {
          const fullRoadmap = await roadmapApi.get(activeRoadmap.id);
          setRoadmap(fullRoadmap);
          setStats(await roadmapApi.getStats(fullRoadmap.id));
        } else {
          setRoadmap(null);
          setStats(null);
        }
      } catch {
        setError("The dashboard summary could not be loaded.");
        toast.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    void fetchDashboardData();
  }, []);

  const allMilestones = useMemo<Array<RoadmapMilestone & { phaseName?: string }>>(() => {
    const milestones: Array<RoadmapMilestone & { phaseName?: string }> = [];

    roadmap?.phases?.forEach((phase) => {
      phase.milestones?.forEach((milestone) => {
        milestones.push({ ...milestone, phaseName: phase.title });
      });
    });

    return milestones;
  }, [roadmap]);

  const completedMilestones = allMilestones
    .filter((milestone) => milestone.status === "completed")
    .slice(0, 4);

  const nextMilestones = allMilestones
    .filter((milestone) => milestone.status === "not_started" || milestone.status === "in_progress")
    .slice(0, 4);

  const activePhase = roadmap?.phases?.find((phase) => phase.id === stats?.current_phase?.id)
    ?? roadmap?.phases?.find((phase) => phase.status === "in_progress")
    ?? roadmap?.phases?.find((phase) => phase.status === "not_started")
    ?? roadmap?.phases?.[0]
    ?? null;

  const completedMilestoneCount = stats?.completed_milestones ?? completedMilestones.length;
  const totalMilestoneCount = stats?.total_milestones ?? allMilestones.length;
  const completedCourseCount = stats?.completed_courses ?? 0;
  const phaseProgress = getPhaseProgress(activePhase, roadmap);
  const nextActionTitle = stats?.next_action?.title ?? roadmap?.journey_summary?.next_action_title ?? "Create your first roadmap";
  const nextActionSummary = stats?.next_action?.summary ?? roadmap?.journey_summary?.next_action_summary
    ?? "Start with an assessment so Sha8alny can turn your goals into a concrete learning path.";
  const roadmapDescription = roadmap?.description
    ?? "The dashboard will become a living atlas once you generate a roadmap from assessment results or a template.";
  const phaseLabel = roadmap?.journey_summary?.focus_label ?? "Active phase";
  const progressNarrative = roadmap
    ? `${completedMilestoneCount} of ${totalMilestoneCount} milestones are already translated into visible forward motion.`
    : "The atlas is ready for your first route. Once a roadmap exists, progress starts reading like a story instead of a spreadsheet.";
  const streakDays = stats?.pace?.current_streak_days ?? 0;
  const loggedHours = stats?.pace?.total_learning_hours ?? 0;
  const paceValue = streakDays > 0
    ? `${streakDays} day streak`
    : loggedHours > 0
      ? `${loggedHours.toFixed(1)}h logged`
      : `${roadmap?.weekly_hours_commitment ?? 0}h planned`;
  const paceSupportingText = streakDays > 0
    ? "Consecutive days of visible activity on the active roadmap."
    : loggedHours > 0
      ? "Time captured against the current roadmap."
      : "Weekly commitment until activity starts showing up as completed work.";

  const routeLinks = roadmap
    ? [
      { label: "Open roadmap", to: ROUTES.roadmap },
      { label: "Explore jobs", to: ROUTES.jobs },
      { label: "Update profile", to: ROUTES.profile },
    ]
    : [
      { label: "Start assessment", to: ROUTES.assessment },
      { label: "Browse templates", to: ROUTES.roadmap },
      { label: "Explore jobs", to: ROUTES.jobs },
    ];

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center px-6">
        <div className="space-y-4 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary" />
          <p className="type-kicker">Preparing your dashboard atlas</p>
          <p className="max-w-md text-sm leading-6 text-muted-foreground">
            Pulling the latest roadmap, milestones, and next-step signals into one readable surface.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-14 pb-12">
      {error ? (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-full border border-destructive/25 bg-destructive/5 px-5 py-3 text-sm">
          <p className="font-medium text-destructive">Dashboard unavailable</p>
          <p className="text-muted-foreground">{error}</p>
        </div>
      ) : null}

      <section className="relative overflow-hidden rounded-[3rem] border border-border/70 bg-card/55 px-6 py-8 shadow-soft-lg backdrop-blur-md sm:px-8 lg:px-12 lg:py-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(244,114,38,0.16),transparent_26%),radial-gradient(circle_at_78%_18%,rgba(13,148,136,0.11),transparent_22%),linear-gradient(180deg,rgba(255,255,255,0.44),transparent_72%)]" />
        <div className="pointer-events-none absolute inset-x-6 top-[38%] h-px bg-border/60 sm:inset-x-8 lg:inset-x-12" />
        <div className="pointer-events-none absolute inset-y-8 left-[46%] hidden w-px bg-border/40 xl:block" />

        <div className="relative space-y-12">
          <div className="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-4xl space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <span className="type-kicker">Dashboard / Career Atlas</span>
                <span className="rounded-full border border-border/60 px-3 py-1 text-xs uppercase tracking-[0.22em] text-muted-foreground">
                  Narrative surface
                </span>
              </div>

              <h1 className="text-balance text-[clamp(3.2rem,9vw,7.3rem)] font-bold leading-[0.86] text-foreground">
                {roadmap
                  ? `${firstName}, your momentum is already visible.`
                  : `${firstName}, let’s map the first direction.`}
              </h1>

              <p className="max-w-2xl text-base leading-7 text-foreground/72 sm:text-lg">
                {progressNarrative}
              </p>
            </div>

            <div className="max-w-md space-y-3 xl:pt-6 xl:text-right">
              <p className="type-kicker">Roadmap title</p>
              <h2 className="text-balance text-3xl font-bold leading-tight text-foreground sm:text-4xl">
                {roadmap?.title ?? "No active roadmap yet"}
              </h2>
              <p className="text-sm leading-6 text-foreground/68 sm:ml-auto sm:max-w-sm">
                {roadmapDescription}
              </p>
            </div>
          </div>

          <div className="grid gap-10 xl:grid-cols-[0.64fr_minmax(0,1.3fr)_0.82fr] xl:items-end">
            <div className="space-y-2">
              <p className="type-kicker">Completed milestones</p>
              <p className="text-[clamp(5rem,15vw,10rem)] font-bold leading-none text-foreground">
                {completedMilestoneCount}
              </p>
              <p className="max-w-[16rem] text-sm leading-6 text-muted-foreground">
                {totalMilestoneCount > 0
                  ? `Out of ${totalMilestoneCount} milestones in the current journey.`
                  : "This number becomes the visual anchor once the roadmap starts moving."}
              </p>
            </div>

            <div className="space-y-5 border-y border-border/60 py-6 lg:py-8">
              <p className="type-kicker">Next action insights</p>
              <div className="max-w-3xl space-y-4">
                <h2 className="text-balance text-3xl font-bold leading-[0.92] text-foreground sm:text-4xl lg:text-5xl">
                  {nextActionTitle}
                </h2>
                <p className="max-w-2xl text-base leading-7 text-foreground/72 sm:text-lg">
                  {nextActionSummary}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background transition-smooth [--interactive-hover-scale:1.014] [--interactive-lift:2px] hover:bg-foreground/90"
                  to={roadmap ? ROUTES.roadmap : ROUTES.assessment}
                >
                  {roadmap ? "Open roadmap" : "Start assessment"}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 px-4 py-3 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/82"
                  to={ROUTES.jobs}
                >
                  Explore jobs
                </Link>
              </div>
            </div>

            <div className="space-y-4 xl:text-right">
              <div>
                <p className="type-kicker">{phaseLabel}</p>
                <p className="mt-3 text-balance text-3xl font-bold leading-tight text-foreground sm:text-4xl">
                  {activePhase?.title ?? "Assessment pending"}
                </p>
                <p className="mt-3 text-sm leading-6 text-foreground/68">
                  {activePhase?.description
                    ?? "Generate a roadmap to reveal the current phase, pacing, and sequence."}
                </p>
              </div>

              <div className="flex items-end gap-3 xl:justify-end">
                <span className="text-6xl font-bold leading-none text-foreground">{phaseProgress}%</span>
                <span className="pb-1 text-sm uppercase tracking-[0.18em] text-muted-foreground">
                  phase progress
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="content-auto grid gap-10 lg:grid-cols-12 lg:items-start">
        <div className="space-y-6 lg:col-span-4">
          <p className="type-kicker">Reading the journey</p>
          <h2 className="text-balance text-4xl font-bold leading-[0.92] text-foreground md:text-5xl">
            The dashboard should guide the eye before it asks for interpretation.
          </h2>
          <p className="max-w-md text-base leading-7 text-foreground/70">
            Instead of stacking widgets, the surface now treats progress, focus, and next action as one continuous editorial composition.
          </p>

          <div className="space-y-5 border-t border-border/60 pt-5">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="type-kicker">Phases complete</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Progress across the broader arc.
                </p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {stats ? `${stats.completed_phases}/${stats.total_phases}` : "0/0"}
              </p>
            </div>

            <div className="flex items-end justify-between gap-4 border-t border-border/50 pt-5">
              <div>
                <p className="type-kicker">Completed courses</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Proof that milestone work reached finished learning material.
                </p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {completedCourseCount}
              </p>
            </div>

            <div className="flex items-end justify-between gap-4 border-t border-border/50 pt-5">
              <div>
                <p className="type-kicker">Learning pace</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {paceSupportingText}
                </p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {paceValue}
              </p>
            </div>

            <div className="flex items-end justify-between gap-4 border-t border-border/50 pt-5">
              <div>
                <p className="type-kicker">Time horizon</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Estimated length of the current route.
                </p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {roadmap?.estimated_duration_weeks ?? 0}w
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-10 lg:col-span-8 xl:grid-cols-[1.08fr_0.92fr]">
          <div className="space-y-5 border-t border-border/60 pt-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="type-kicker">Completed milestones</p>
                <h3 className="mt-3 text-2xl font-bold text-foreground sm:text-3xl">
                  The work already finished.
                </h3>
              </div>
              <p className="max-w-xs text-sm leading-6 text-muted-foreground sm:text-right">
                Visible wins make the next phase feel earned instead of abstract.
              </p>
            </div>

            {completedMilestones.length > 0 ? (
              <ol className="space-y-5">
                {completedMilestones.map((milestone, index) => (
                  <li
                    className="grid gap-3 border-t border-border/40 pt-4 sm:grid-cols-[84px_minmax(0,1fr)] sm:items-start"
                    key={milestone.id}
                  >
                    <div className="text-[2.6rem] font-bold leading-none text-foreground/18">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <div className="space-y-2">
                      <p className="text-xl font-semibold leading-tight text-foreground">
                        {milestone.title}
                      </p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        <span>{milestone.phaseName ?? "Current route"}</span>
                        <span>{milestone.estimated_duration_hours}h effort</span>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="border-t border-border/40 pt-4 text-sm leading-6 text-muted-foreground">
                Completed milestones will start filling this editorial timeline once progress begins.
              </p>
            )}
          </div>

          <div className="space-y-8 border-t border-border/60 pt-5">
            <div className="space-y-3">
              <p className="type-kicker">Active phase</p>
              <h3 className="text-balance text-3xl font-bold leading-[0.92] text-foreground sm:text-4xl">
                {activePhase?.title ?? "Your roadmap focus will appear here."}
              </h3>
              <p className="max-w-md text-base leading-7 text-foreground/70">
                {activePhase?.description
                  ?? "As soon as a roadmap is active, this area becomes the editorial anchor for the work in motion."}
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="type-kicker">Next queue</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    What the atlas suggests you touch next.
                  </p>
                </div>
                <p className="text-xl font-semibold text-foreground">
                  {nextMilestones.length} queued
                </p>
              </div>

              {nextMilestones.length > 0 ? (
                <div className="space-y-4">
                  {nextMilestones.map((milestone) => (
                    <div className="border-t border-border/40 pt-4" key={milestone.id}>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-lg font-semibold leading-tight text-foreground">
                            {milestone.title}
                          </p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {milestone.phaseName ?? activePhase?.title ?? "Current route"}
                          </p>
                        </div>
                        <span className="text-sm uppercase tracking-[0.18em] text-muted-foreground">
                          {milestone.estimated_duration_hours}h
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="border-t border-border/40 pt-4 text-sm leading-6 text-muted-foreground">
                  Once milestones are queued, the next sequence appears here instead of hiding inside a widget stack.
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="content-auto border-y border-border/60 py-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <p className="type-kicker">Continue from here</p>
            <h2 className="text-balance text-2xl font-bold text-foreground sm:text-3xl">
              The dashboard points forward, but the real work happens in the next surface.
            </h2>
          </div>

          <div className="flex flex-wrap gap-6">
            {routeLinks.map((link) => (
              <Link
                className="focus-ring interactive-scale inline-flex items-center gap-2 text-lg font-semibold text-foreground transition-smooth [--interactive-hover-scale:1.008] hover:text-primary"
                key={link.to}
                to={link.to}
              >
                {link.label}
                <ArrowRight className="h-4 w-4" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {!roadmap ? (
        <section className="content-auto shadow-card relative overflow-hidden rounded-[2.4rem] border border-dashed border-border/70 px-6 py-8 sm:px-8">
          <div className="pointer-events-none absolute right-6 top-6 text-[7rem] font-bold leading-none text-foreground/6 sm:text-[9rem]">
            00
          </div>
          <div className="relative max-w-3xl space-y-5">
            <p className="type-kicker">No active roadmap</p>
            <h2 className="text-balance text-3xl font-bold leading-[0.92] text-foreground sm:text-4xl">
              Start with assessment, then let the atlas take over.
            </h2>
            <p className="max-w-2xl text-base leading-7 text-foreground/70">
              Without a roadmap, the dashboard stays intentionally spare. The first meaningful step is generating a path that can expose milestones, pace, and focus.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-3 text-sm font-medium text-background transition-smooth [--interactive-hover-scale:1.014] [--interactive-lift:2px] hover:bg-foreground/90"
                to={ROUTES.assessment}
              >
                Begin assessment
                <Compass className="h-4 w-4" />
              </Link>
              <Link
                className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 px-4 py-3 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/82"
                to={ROUTES.roadmap}
              >
                Browse templates
                <Sparkles className="h-4 w-4 text-primary" />
              </Link>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
