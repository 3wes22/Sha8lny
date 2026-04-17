import { Loader2 } from "lucide-react";

interface AnalyzingTransitionProps {
  stage: "stage_1" | "stage_2";
}

export function AnalyzingTransition({ stage }: AnalyzingTransitionProps) {
  const title =
    stage === "stage_1" ? "Analyzing your responses" : "Finalizing your assessment";
  const description =
    stage === "stage_1"
      ? "We’re reviewing your first-stage answers to generate targeted follow-up questions."
      : "We’re combining both stages into your roadmap-ready assessment result.";

  return (
    <section className="poster-surface overflow-hidden rounded-[2rem] border border-border/70">
      <div className="grid gap-6 px-6 py-8 md:px-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <p className="type-kicker">Assessment analysis</p>
          <h1 className="text-balance text-4xl font-bold md:text-5xl">{title}</h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            {description}
          </p>
        </div>
        <div className="atlas-panel flex items-center gap-4 p-5">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <div className="space-y-1">
            <p className="text-sm font-semibold">Stage transition in progress</p>
            <p className="text-sm text-muted-foreground">
              {stage === "stage_1" ? "Stage 1 complete, preparing stage 2." : "Stage 2 complete, preparing results."}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
