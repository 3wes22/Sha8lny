import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { useAuth } from "@/features/auth/context/AuthContext";
import { roadmapApi, type Roadmap, type RoadmapMilestone, type RoadmapPhase, type RoadmapStats } from "@/lib/api";
import { toast } from "sonner";

import { DashboardFocusCard } from "../components/DashboardFocusCard";
import { DashboardStatRow } from "../components/DashboardStatRow";
import { DashboardUpNext } from "../components/DashboardUpNext";
import { DashboardWelcome } from "../components/DashboardWelcome";

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

  const nextMilestones = allMilestones
    .filter((milestone) => milestone.status === "not_started" || milestone.status === "in_progress")
    .slice(0, 3);

  const activePhase = roadmap?.phases?.find((phase) => phase.id === stats?.current_phase?.id)
    ?? roadmap?.phases?.find((phase) => phase.status === "in_progress")
    ?? roadmap?.phases?.find((phase) => phase.status === "not_started")
    ?? roadmap?.phases?.[0]
    ?? null;

  const completedMilestoneCount = stats?.completed_milestones ?? allMilestones.filter((m) => m.status === "completed").length;
  const totalMilestoneCount = stats?.total_milestones ?? allMilestones.length;
  const completionPercent = Math.round(Number(roadmap?.completion_percentage ?? 0));
  const phaseProgress = getPhaseProgress(activePhase, roadmap);
  const nextActionTitle = stats?.next_action?.title ?? roadmap?.journey_summary?.next_action_title ?? "Continue your journey";

  const streakDays = stats?.pace?.current_streak_days ?? 0;
  const loggedHours = stats?.pace?.total_learning_hours ?? 0;
  const paceValue = streakDays > 0
    ? `${streakDays} day streak`
    : loggedHours > 0
      ? `${loggedHours.toFixed(1)}h logged`
      : `${roadmap?.weekly_hours_commitment ?? 0}h planned`;

  const greeting = `Welcome back, ${firstName}.`;
  const statusText = roadmap
    ? `You're ${completionPercent}% through ${roadmap.title}. Next up: ${nextActionTitle}.`
    : "Map your first direction — start with an assessment so Sha8alny can turn your goals into a concrete learning path.";

  const statItems = [
    { label: "Milestones", value: `${completedMilestoneCount}/${totalMilestoneCount}` },
    { label: "Phases", value: stats ? `${stats.completed_phases}/${stats.total_phases}` : "0/0" },
    { label: "Pace", value: paceValue },
    { label: "Horizon", value: `${roadmap?.estimated_duration_weeks ?? 0}w` },
  ];

  const routeLinks = roadmap
    ? [
      { label: "Open roadmap", to: ROUTES.roadmap },
      { label: "Explore jobs", to: ROUTES.jobs },
      { label: "Ask the advisor", to: ROUTES.advisor },
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
          <p className="type-kicker">Preparing your dashboard</p>
          <p className="max-w-md text-sm leading-6 text-muted-foreground">
            Pulling your latest roadmap, milestones, and next-step signals into one readable surface.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[760px] space-y-5 pb-12">
      {error ? (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-full border border-destructive/25 bg-destructive/5 px-5 py-3 text-sm">
          <p className="font-medium text-destructive">Dashboard unavailable</p>
          <p className="text-muted-foreground">{error}</p>
        </div>
      ) : null}

      <DashboardWelcome
        greeting={greeting}
        statusText={statusText}
        primaryLabel={roadmap ? "Open roadmap" : "Start assessment"}
        primaryTo={roadmap ? ROUTES.roadmap : ROUTES.assessment}
      />

      <DashboardStatRow items={statItems} />

      <DashboardFocusCard
        title={activePhase?.title ?? (roadmap ? "Roadmap in progress" : "No active roadmap yet")}
        description={
          activePhase?.description
          ?? "Generate a roadmap from your assessment to reveal the current phase, pacing, and sequence."
        }
        progress={phaseProgress}
      />

      <DashboardUpNext
        milestones={nextMilestones}
        fallbackText={
          roadmap
            ? "No milestones are queued right now. New steps will appear here as your phase progresses."
            : "Once a roadmap exists, your next milestones will line up here."
        }
      />

      <section className="panel-paper rounded-[1.6rem] px-6 py-6 sm:px-7">
        <p className="type-kicker">Continue exploring</p>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-3">
          {routeLinks.map((link) => (
            <Link
              className="focus-ring interactive-scale inline-flex items-center gap-1.5 text-sm font-semibold text-foreground transition-smooth [--interactive-hover-scale:1.01] hover:text-primary"
              key={link.to}
              to={link.to}
            >
              {link.label}
              <ArrowRight className="h-4 w-4" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
