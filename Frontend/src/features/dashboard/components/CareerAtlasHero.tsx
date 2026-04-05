import { ArrowRight, Compass, Sparkles, Timer } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Roadmap, RoadmapStats } from "@/lib/api";

interface CareerAtlasHeroProps {
  firstName: string;
  roadmap: Roadmap | null;
  stats: RoadmapStats | null;
}

export function CareerAtlasHero({ firstName, roadmap, stats }: CareerAtlasHeroProps) {
  const progress = Number(roadmap?.completion_percentage ?? 0);
  const nextAction = roadmap?.journey_summary?.next_action_title ?? "Create your first roadmap";

  return (
    <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70">
      <div className="relative grid gap-8 px-6 py-8 md:px-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="relative z-10 space-y-5 motion-rise">
          <Badge className="w-fit border-primary/20 bg-primary/10 text-primary" variant="outline">
            <Sparkles className="mr-2 h-3.5 w-3.5" />
            Your current position
          </Badge>
          <div className="space-y-3">
            <h2 className="text-balance text-4xl font-bold md:text-6xl">
              {firstName}, your next career move is already mapped.
            </h2>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              Sha8alny translates assessments, learning milestones, and job signals into one readable path.
              The roadmap is your operating surface, not just another dashboard tile.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button asChild className="gradient-primary">
              <Link to={roadmap ? ROUTES.roadmap : ROUTES.assessment}>
                {roadmap ? "Open roadmap" : "Start assessment"}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to={ROUTES.jobs}>Explore jobs</Link>
            </Button>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Completion</p>
              <p className="mt-2 text-3xl font-bold">{progress.toFixed(0)}%</p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Milestones</p>
              <p className="mt-2 text-3xl font-bold">
                {stats ? `${stats.completed_milestones}/${stats.total_milestones}` : "0/0"}
              </p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <p className="type-kicker">Study pace</p>
              <p className="mt-2 text-3xl font-bold">{roadmap?.weekly_hours_commitment ?? 0}h</p>
            </div>
          </div>
        </div>

        <div className="relative z-10 grid gap-4 motion-fade">
          <div className="atlas-panel bg-card/90 p-5">
            <p className="type-kicker">Current roadmap</p>
            <h3 className="mt-3 text-2xl font-bold">{roadmap?.title ?? "No active roadmap yet"}</h3>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {roadmap?.description ?? "Start with an assessment or template to generate your first career journey."}
            </p>
            <div className="mt-4 flex items-center gap-3 text-sm text-muted-foreground">
              <Compass className="h-4 w-4 text-primary" />
              <span>{nextAction}</span>
            </div>
          </div>

          <div className="atlas-panel bg-foreground px-5 py-6 text-background">
            <p className="type-kicker text-background/60">Time horizon</p>
            <div className="mt-3 flex items-center gap-3">
              <Timer className="h-5 w-5 text-primary" />
              <p className="text-2xl font-bold">
                {roadmap ? `${roadmap.estimated_duration_weeks} weeks planned` : "Career plan pending"}
              </p>
            </div>
            <p className="mt-3 text-sm leading-6 text-background/70">
              The atlas view emphasizes sequence, pace, and next action so you can move from assessment to execution without losing context.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
