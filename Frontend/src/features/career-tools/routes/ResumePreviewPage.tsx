import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Download, Edit, FileText, Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { resumeApi, type Resume as ResumeType, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { toast } from "sonner";

export default function ResumePreviewPage() {
  const { resumeId } = useParams<{ resumeId: string }>();
  const [resume, setResume] = useState<ResumeType | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [optimizing, setOptimizing] = useState(false);

  useEffect(() => {
    if (!resumeId) return;
    const load = async () => {
      try {
        const data = await resumeApi.get(resumeId);
        setResume(data);
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to load resume"));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [resumeId]);

  const handleGenerate = async (format: "pdf" | "docx") => {
    if (!resumeId) return;
    setGenerating(format);
    try {
      const result = await resumeApi.generateFile(resumeId, format);
      toast.success(`${format.toUpperCase()} generated!`);
      if (result.file_url) {
        window.open(result.file_url, "_blank");
      }
      // Refresh resume to get updated file info
      const updated = await resumeApi.get(resumeId);
      setResume(updated);
    } catch (error) {
      toast.error(getApiErrorMessage(error, `Failed to generate ${format.toUpperCase()}`));
    } finally {
      setGenerating(null);
    }
  };

  const handleOptimize = async () => {
    if (!resumeId) return;
    setOptimizing(true);
    try {
      const result = await resumeApi.optimizeATS(resumeId);
      toast.success(`ATS Score: ${result.ats_grade} (${result.ats_score}/100)`);
      // Refresh
      const updated = await resumeApi.get(resumeId);
      setResume(updated);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "ATS optimization failed"));
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!resume) {
    return (
      <StatePanel
        description="The resume you're looking for doesn't exist."
        state="error"
        title="Resume not found"
      />
    );
  }

  const personal = (resume.personal_info || {}) as Record<string, string>;
  const skills = resume.skills as { items?: string[] };
  const skillList = skills?.items ?? [];

  return (
    <PageShell
      actions={
        <div className="flex flex-wrap gap-2">
          <Link to={`/career-tools/resumes/${resumeId}/edit`}>
            <Button variant="outline">
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </Link>
          <Button
            disabled={generating === "pdf"}
            onClick={() => handleGenerate("pdf")}
            variant="outline"
          >
            {generating === "pdf" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            PDF
          </Button>
          <Button
            disabled={generating === "docx"}
            onClick={() => handleGenerate("docx")}
            variant="outline"
          >
            {generating === "docx" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileText className="mr-2 h-4 w-4" />
            )}
            DOCX
          </Button>
          <Button disabled={optimizing} onClick={handleOptimize}>
            {optimizing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            ATS Optimize
          </Button>
        </div>
      }
      description={`${resume.template_name} template · v${resume.version} · ${Math.round(resume.completeness)}% complete`}
      eyebrow="Resume Preview"
      title={resume.title}
    >
      {/* ATS Score (if optimized) */}
      {resume.is_ats_optimized && resume.ats_score !== null ? (
        <div className="atlas-panel p-6">
          <p className="type-kicker">ATS Analysis</p>
          <div className="mt-4 flex items-center gap-6">
            <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-primary">
              <span className="text-2xl font-bold">{resume.ats_grade}</span>
            </div>
            <div>
              <p className="text-3xl font-bold">{resume.ats_score}/100</p>
              <p className="text-sm text-muted-foreground">ATS Compatibility Score</p>
            </div>
          </div>
          {(resume.ats_suggestions as { improvements?: string[] })?.improvements ? (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium">Suggestions:</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {(resume.ats_suggestions as { improvements: string[] }).improvements.map(
                  (s, i) => (
                    <li key={i}>{s}</li>
                  )
                )}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Personal Info */}
      <div className="atlas-panel p-6">
        <p className="type-kicker">Personal Information</p>
        <h2 className="mt-3 text-2xl font-bold">
          {personal.name || "Your Name"}
        </h2>
        <p className="mt-1 text-muted-foreground">
          {[personal.email, personal.phone, personal.location].filter(Boolean).join(" · ")}
        </p>
        {personal.summary ? (
          <p className="mt-4 leading-7 text-foreground/80">{personal.summary}</p>
        ) : null}
      </div>

      {/* Skills */}
      {skillList.length > 0 ? (
        <div className="atlas-panel p-6">
          <p className="type-kicker">Skills</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {skillList.map((skill) => (
              <Badge className="px-3 py-1" key={typeof skill === 'string' ? skill : JSON.stringify(skill)} variant="outline">
                {typeof skill === "string" ? skill : (skill as { name?: string }).name ?? ""}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
    </PageShell>
  );
}
