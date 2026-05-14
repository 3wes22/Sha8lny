import { Link } from "react-router-dom";
import { FileText, Star } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { ResumeListItem } from "@/lib/api";

interface ResumeCardProps {
  resume: ResumeListItem;
}

const gradeColor: Record<string, string> = {
  A: "bg-emerald-500/15 text-emerald-700 border-emerald-500/30",
  B: "bg-blue-500/15 text-blue-700 border-blue-500/30",
  C: "bg-amber-500/15 text-amber-700 border-amber-500/30",
  D: "bg-orange-500/15 text-orange-700 border-orange-500/30",
  F: "bg-red-500/15 text-red-700 border-red-500/30",
};

export function ResumeCard({ resume }: ResumeCardProps) {
  return (
    <Link
      className="atlas-panel group block p-5 transition-smooth interactive-scale [--interactive-lift:2px]"
      to={`/career-tools/resumes/${resume.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-primary/10 p-3">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0 space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="truncate text-lg font-semibold">{resume.title}</h3>
              {resume.is_primary ? (
                <Star className="h-4 w-4 shrink-0 fill-amber-400 text-amber-400" />
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground">
              {resume.template_name} template · v{resume.version}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {resume.is_ats_optimized && resume.ats_grade ? (
            <Badge
              className={gradeColor[resume.ats_grade] ?? ""}
              variant="outline"
            >
              ATS {resume.ats_grade}
            </Badge>
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex items-center gap-6 text-sm text-muted-foreground">
        <span>{Math.round(resume.completeness)}% complete</span>
        <span>Updated {new Date(resume.updated_at).toLocaleDateString()}</span>
      </div>

      {/* Completeness bar */}
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted/50">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${resume.completeness}%` }}
        />
      </div>
    </Link>
  );
}
