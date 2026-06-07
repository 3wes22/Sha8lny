import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";

export interface JobMatchExplanationData {
  matching_skills?: string[];
  missing_skills?: string[];
  top_factors?: Array<{
    feature: string;
    value: number;
    contribution?: number;
  }>;
  experience_fit?: string;
  user_career_level?: string;
  job_experience_level?: string;
}

const formatFeature = (name: string) =>
  name
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

interface JobMatchExplanationProps {
  explanation?: JobMatchExplanationData | null;
  matchingSkills?: string[];
  missingSkills?: string[];
}

export function JobMatchExplanation({
  explanation,
  matchingSkills = [],
  missingSkills = [],
}: JobMatchExplanationProps) {
  const [open, setOpen] = useState(false);
  const resolved = explanation ?? {
    matching_skills: matchingSkills,
    missing_skills: missingSkills,
    top_factors: [],
  };
  const matched = resolved.matching_skills ?? matchingSkills;
  const missing = resolved.missing_skills ?? missingSkills;
  const factors = resolved.top_factors ?? [];

  const levelNote =
    resolved.user_career_level && resolved.job_experience_level
      ? `Level fit: ${resolved.job_experience_level} role for your ${resolved.user_career_level} profile`
      : null;

  if (!matched.length && !missing.length && !factors.length && !levelNote) {
    return null;
  }

  return (
    <div className="mt-3 rounded-lg border border-border/60 bg-muted/30 p-3">
      <button
        className="flex h-auto w-full items-center justify-between rounded-md px-1 py-1 text-left text-sm font-semibold text-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <span>Why this match?</span>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {open ? (
        <div className="mt-3 space-y-3 text-sm">
          {levelNote ? <p className="text-muted-foreground">{levelNote}</p> : null}
          {matched.length > 0 ? (
            <div>
              <p className="mb-1 font-medium text-foreground">Skills you have</p>
              <div className="flex flex-wrap gap-1">
                {matched.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}

          {missing.length > 0 ? (
            <div>
              <p className="mb-1 font-medium text-foreground">Gaps to close</p>
              <div className="flex flex-wrap gap-1">
                {missing.map((skill) => (
                  <Badge key={skill} variant="outline">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}

          {factors.length > 0 ? (
            <div>
              <p className="mb-1 font-medium text-foreground">Top ranking signals</p>
              <ul className="list-inside list-disc text-muted-foreground">
                {factors.map((factor) => (
                  <li key={factor.feature}>
                    {formatFeature(factor.feature)} ({factor.value.toFixed(2)})
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
