import { BriefcaseBusiness, Loader2, Map, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import type { AssessmentResult } from "@/lib/api";

interface AssessmentResultHeroProps {
  result: AssessmentResult;
  onCreateRoadmap?: () => void;
  creatingRoadmap?: boolean;
}

export function AssessmentResultHero({
  result,
  onCreateRoadmap,
  creatingRoadmap = false,
}: AssessmentResultHeroProps) {
  const confidenceLabel = result.ai_confidence_score
    ? `${Math.round(result.ai_confidence_score)}%`
    : result.roadmap_signal
      ? `${Math.round(result.roadmap_signal.confidence_score * 100)}%`
      : "Signal ready";

  return (
    <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70">
      <div className="relative grid gap-8 px-6 py-8 md:px-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="relative z-10 space-y-5 motion-rise">
          <p className="type-kicker">Assessment outcome</p>
          <h1 className="text-balance text-4xl font-bold md:text-6xl">
            {result.status_message ?? "Your assessment is ready."}
          </h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            {result.ai_insights}
          </p>
          <div className="flex flex-wrap gap-3">
            {onCreateRoadmap ? (
              <Button className="gradient-primary" disabled={creatingRoadmap} onClick={onCreateRoadmap}>
                {creatingRoadmap ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Map className="mr-2 h-4 w-4" />}
                Generate personalized roadmap
              </Button>
            ) : (
              <Button asChild className="gradient-primary">
                <Link to={ROUTES.roadmap}>
                  View roadmap
                  <Map className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            )}
            <Button asChild variant="outline">
              <Link to={ROUTES.jobs}>
                Explore jobs
                <BriefcaseBusiness className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
        <div className="relative z-10 grid gap-3 self-end">
          <div className="atlas-panel p-5">
            <p className="type-kicker">Overall score</p>
            <p className="mt-3 text-5xl font-bold">{Number(result.overall_score).toFixed(0)}%</p>
          </div>
          <div className="atlas-panel p-5">
            <div className="flex items-center gap-2 text-primary">
              <Sparkles className="h-4 w-4" />
              <p className="text-sm font-semibold">Confidence</p>
            </div>
            <p className="mt-3 text-2xl font-bold">
              {confidenceLabel}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
