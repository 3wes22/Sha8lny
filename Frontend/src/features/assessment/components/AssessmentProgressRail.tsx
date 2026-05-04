import { Progress } from "@/components/ui/progress";
import type { Assessment } from "@/lib/api";

interface AssessmentProgressRailProps {
  assessment: Assessment;
  currentIndex: number;
  answeredCount: number;
}

export function AssessmentProgressRail({
  assessment,
  currentIndex,
  answeredCount,
}: AssessmentProgressRailProps) {
  const totalQuestions = assessment.questions.length;
  const progressValue = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;
  const stageLabel = assessment.stage === "stage_2" ? "Stage 2 of 2" : "Stage 1 of 2";

  return (
    <div className="atlas-panel p-5">
      <p className="type-kicker">Assessment rail</p>
      <div className="mt-4 space-y-4">
        <div>
          <p className="text-sm uppercase tracking-[0.18em] text-muted-foreground">{stageLabel}</p>
          <p className="text-sm font-semibold">
            Question {currentIndex + 1} of {totalQuestions}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {answeredCount} responses captured so far.
          </p>
        </div>
        <Progress className="h-2" value={progressValue} />
        <div className="rounded-[1.25rem] bg-muted/45 p-4">
          <p className="type-kicker">State</p>
          <p className="mt-2 text-lg font-semibold">
            {assessment.presentation?.submission_state === "completed" ? "Complete" : "In progress"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Answers are used to build your roadmap and next-step recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}
