import { ClipboardCheck, Sparkles, Timer } from "lucide-react";

import { JourneyProgress } from "@/shared/components/JourneyProgress";

export function AssessmentIntroHero() {
  return (
    <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70">
      <div className="relative grid gap-8 px-6 py-8 md:px-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="relative z-10 space-y-5 motion-rise">
          <p className="type-kicker">Assessment</p>
          <h1 className="text-balance text-4xl font-bold md:text-6xl">
            Diagnose your current readiness before committing to a path.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            The assessment should feel structured and premium: fast to scan, confident in tone, and explicit about what happens before, during, and after submission.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel-paper rounded-[1.5rem] p-4">
              <ClipboardCheck className="h-5 w-5 text-primary" />
              <p className="mt-3 text-lg font-semibold">Targeted questions</p>
              <p className="mt-1 text-sm text-muted-foreground">Focused around career readiness and skill confidence.</p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <Timer className="h-5 w-5 text-primary" />
              <p className="mt-3 text-lg font-semibold">Short sessions</p>
              <p className="mt-1 text-sm text-muted-foreground">Designed to be completed in one sitting.</p>
            </div>
            <div className="panel-paper rounded-[1.5rem] p-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <p className="mt-3 text-lg font-semibold">Actionable outcome</p>
              <p className="mt-1 text-sm text-muted-foreground">Each result points toward roadmap or job next steps.</p>
            </div>
          </div>
        </div>

        <div className="relative z-10 self-end">
          <JourneyProgress
            steps={[
              { id: "1", label: "Choose path", status: "complete" },
              { id: "2", label: "Answer", status: "current" },
              { id: "3", label: "Process", status: "upcoming" },
              { id: "4", label: "Act", status: "upcoming" },
            ]}
          />
        </div>
      </div>
    </section>
  );
}
