import { Badge } from "@/components/ui/badge";
import type { AssessmentResult } from "@/lib/api";

interface AssessmentOutcomeCardsProps {
  result: AssessmentResult;
}

function humanizeSignalKey(value: string) {
  return value.replaceAll("_", " ");
}

export function AssessmentOutcomeCards({ result }: AssessmentOutcomeCardsProps) {
  const prioritySkills = result.roadmap_signal?.priority_order ?? [];

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="atlas-panel p-5">
        <p className="type-kicker">Strengths</p>
        <div className="mt-4 space-y-2">
          {result.strengths.map((strength) => (
            <div className="rounded-[1.25rem] bg-success/10 p-3" key={strength}>
              <p className="font-medium">{strength}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="atlas-panel p-5">
        <p className="type-kicker">Growth areas</p>
        <div className="mt-4 space-y-2">
          {result.areas_for_improvement.map((area) => (
            <div className="rounded-[1.25rem] bg-muted/50 p-3" key={area}>
              <p className="font-medium">{area}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="atlas-panel p-5">
        <p className="type-kicker">Roadmap priorities</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {prioritySkills.length > 0
            ? prioritySkills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {humanizeSignalKey(skill)}
                </Badge>
              ))
            : result.top_skills.map((skill) => (
                <Badge key={`${skill.skill}-${skill.score}`} variant="outline">
                  {skill.skill} {skill.score}%
                </Badge>
              ))}
        </div>
      </div>
    </div>
  );
}
