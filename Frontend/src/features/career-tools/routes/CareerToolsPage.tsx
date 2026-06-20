import React, { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Copy,
  FileText,
  Globe,
  Loader2,
  Lock,
  Plus,
  Sparkles,
  Trash2,
  Upload,
  Wand2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageShell } from "@/shared/components/PageShell";
import { SectionHeader } from "@/shared/components/SectionHeader";
import { StatePanel } from "@/shared/components/StatePanel";
import { cn } from "@/lib/utils";
import {
  careerToolsApi,
  getApiErrorMessage,
  type AtsResult,
  type PortfolioListItem,
  type ResumeImprovement,
  type ResumeListItem,
} from "@/lib/api";

const gradeTone = (grade?: string) => {
  switch ((grade ?? "").charAt(0).toUpperCase()) {
    case "A":
      return "text-success";
    case "B":
      return "text-primary";
    case "C":
      return "text-warning";
    default:
      return "text-muted-foreground";
  }
};

const copyText = async (label: string, text: string) => {
  if (!text.trim()) return;
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  } catch {
    toast.error("Couldn't copy to clipboard");
  }
};

const buildSuggestionText = (improvement: ResumeImprovement): string => {
  const parts: string[] = [];
  if (improvement.improved_summary) {
    parts.push(`SUMMARY\n${improvement.improved_summary}`);
  }
  if (improvement.strengthened_bullets.length) {
    parts.push(`STRONGER BULLETS\n${improvement.strengthened_bullets.map((b) => `• ${b}`).join("\n")}`);
  }
  if (improvement.missing_keywords.length) {
    parts.push(`MISSING KEYWORDS\n${improvement.missing_keywords.join(", ")}`);
  }
  if (improvement.recommendations.length) {
    parts.push(`RECOMMENDATIONS\n${improvement.recommendations.map((r) => `• ${r}`).join("\n")}`);
  }
  return parts.join("\n\n");
};

const ResumeCard: React.FC<{
  resume: ResumeListItem;
  ats?: AtsResult;
  improvement?: ResumeImprovement;
  busy: boolean;
  onImprove: () => void;
  onDelete: () => void;
}> = ({ resume, ats, improvement, busy, onImprove, onDelete }) => {
  const score = improvement ? improvement.ats_score : ats ? ats.ats_score : Number(resume.ats_score);
  const grade = improvement ? improvement.ats_grade : ats ? ats.ats_grade : resume.ats_grade;

  return (
    <div className="panel-paper card-elevated flex flex-col gap-4 rounded-[1.5rem] p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="rounded-2xl bg-background/80 p-3 text-primary">
            <FileText className="h-5 w-5" />
          </span>
          <div>
            <h3 className="text-lg font-semibold leading-tight">{resume.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {resume.template_name ?? "default"} template
              {resume.is_primary ? " · primary" : ""}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className={cn("text-2xl font-bold", gradeTone(grade))}>{Math.round(Number(score) || 0)}</p>
          <p className="type-kicker text-[0.6rem]">ATS {grade ?? "—"}</p>
        </div>
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
          <span>Completeness</span>
          <span>{Math.round(resume.completeness ?? 0)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="gradient-primary h-full rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, resume.completeness ?? 0))}%` }}
          />
        </div>
      </div>

      {improvement ? (
        <div className="space-y-4 rounded-2xl bg-background/60 p-4 text-sm">
          {!improvement.ai_used ? (
            <p className="rounded-lg bg-warning/10 px-3 py-2 text-xs text-warning">
              AI is offline right now — showing a deterministic checklist instead.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Suggestions only — copy what you like into your CV. Nothing here changes your saved resume.
            </p>
          )}

          {improvement.improved_summary ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <p className="type-kicker text-[0.6rem]">Suggested summary</p>
                <button
                  className="transition-smooth flex items-center gap-1 text-xs text-muted-foreground hover:text-primary"
                  onClick={() => void copyText("Summary", improvement.improved_summary)}
                  type="button"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy
                </button>
              </div>
              <p className="rounded-lg border border-primary/30 bg-primary/5 p-2 text-foreground">
                {improvement.improved_summary}
              </p>
            </div>
          ) : null}

          {improvement.strengthened_bullets.length ? (
            <div className="space-y-1.5">
              <p className="type-kicker text-[0.6rem]">Stronger bullets</p>
              <ul className="space-y-1">
                {improvement.strengthened_bullets.map((bullet) => (
                  <li className="flex items-start gap-2 text-muted-foreground" key={bullet}>
                    <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {improvement.missing_keywords.length ? (
            <div className="space-y-1.5">
              <p className="type-kicker text-[0.6rem]">Missing keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {improvement.missing_keywords.map((keyword) => (
                  <span
                    className="rounded-full border border-border/70 bg-background/80 px-2 py-0.5 text-xs"
                    key={keyword}
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {improvement.recommendations.length ? (
            <div className="space-y-1.5">
              <p className="type-kicker text-[0.6rem]">Recommendations</p>
              <ul className="space-y-1">
                {improvement.recommendations.map((rec) => (
                  <li className="flex items-start gap-2 text-muted-foreground" key={rec}>
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <Button
            className="w-full"
            onClick={() => void copyText("All suggestions", buildSuggestionText(improvement))}
            size="sm"
            variant="outline"
          >
            <Copy className="mr-1 h-4 w-4" />
            Copy all suggestions
          </Button>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        <Button className="flex-1" disabled={busy} onClick={onImprove} size="sm" variant="outline">
          {busy ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Wand2 className="mr-1 h-4 w-4" />}
          Improve with AI
        </Button>
        <Button
          aria-label={`Delete ${resume.title}`}
          disabled={busy}
          onClick={onDelete}
          size="sm"
          variant="ghost"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
};

const PortfolioCard: React.FC<{
  portfolio: PortfolioListItem;
  publishing: boolean;
  deleting: boolean;
  onPublish: () => void;
  onDelete: () => void;
}> = ({ portfolio, publishing, deleting, onPublish, onDelete }) => (
  <div className="panel-paper card-elevated flex flex-col gap-4 rounded-[1.5rem] p-5">
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-start gap-3">
        <span className="rounded-2xl bg-background/80 p-3 text-primary">
          {portfolio.is_public ? <Globe className="h-5 w-5" /> : <Lock className="h-5 w-5" />}
        </span>
        <div>
          <h3 className="text-lg font-semibold leading-tight">{portfolio.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {portfolio.is_public ? "Public" : "Private"} · {portfolio.view_count} views
          </p>
        </div>
      </div>
      {portfolio.is_public ? <CheckCircle2 className="h-5 w-5 text-success" /> : null}
    </div>

    <div className="flex items-center gap-2">
      <Button
        className="flex-1"
        disabled={publishing || portfolio.is_public}
        onClick={onPublish}
        size="sm"
        variant="outline"
      >
        {publishing ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Globe className="mr-1 h-4 w-4" />}
        {portfolio.is_public ? "Published" : "Publish"}
      </Button>
      <Button
        aria-label={`Delete ${portfolio.title}`}
        disabled={deleting}
        onClick={onDelete}
        size="sm"
        variant="ghost"
      >
        {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
      </Button>
    </div>
  </div>
);

const CareerToolsPage: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [portfolios, setPortfolios] = useState<PortfolioListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [atsResults, setAtsResults] = useState<Record<string, AtsResult>>({});
  const [improvements, setImprovements] = useState<Record<string, ResumeImprovement>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [newResumeTitle, setNewResumeTitle] = useState("");
  const [newPortfolioTitle, setNewPortfolioTitle] = useState("");
  const [creatingResume, setCreatingResume] = useState(false);
  const [creatingPortfolio, setCreatingPortfolio] = useState(false);
  const [resumeMode, setResumeMode] = useState<"create" | "upload">("upload");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshResumes = async () => {
    const response = await careerToolsApi.listResumes();
    setResumes(response.results ?? []);
  };

  const refreshPortfolios = async () => {
    const response = await careerToolsApi.listPortfolios();
    setPortfolios(response.results ?? []);
  };

  useEffect(() => {
    let active = true;
    Promise.all([careerToolsApi.listResumes(), careerToolsApi.listPortfolios()])
      .then(([resumeData, portfolioData]) => {
        if (!active) return;
        setResumes(resumeData.results ?? []);
        setPortfolios(portfolioData.results ?? []);
      })
      .catch((error) => {
        if (active) toast.error(getApiErrorMessage(error, "Failed to load career tools"));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleCreateResume = async () => {
    if (!newResumeTitle.trim()) return;
    try {
      setCreatingResume(true);
      await careerToolsApi.createResume({ title: newResumeTitle.trim() });
      setNewResumeTitle("");
      await refreshResumes();
      toast.success("Resume created");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create resume"));
    } finally {
      setCreatingResume(false);
    }
  };

  const handleUploadResume = async (file: File) => {
    try {
      setUploading(true);
      const resume = await careerToolsApi.uploadResume(file);
      await refreshResumes();
      if (resume.ats_score != null) {
        setAtsResults((prev) => ({
          ...prev,
          [resume.id]: {
            message: "Upload complete",
            ats_score: Number(resume.ats_score),
            ats_grade: resume.ats_grade ?? "",
            suggestions: (resume.ats_suggestions as { improvements?: string[] })?.improvements ?? [],
          },
        }));
      }
      toast.success(`CV uploaded — ATS score ${Math.round(Number(resume.ats_score) || 0)}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to upload CV"));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      void handleUploadResume(file);
    }
  };

  const handleImprove = async (id: string) => {
    try {
      setBusyId(id);
      const improvement = await careerToolsApi.improveResume(id);
      setImprovements((prev) => ({ ...prev, [id]: improvement }));
      toast.success(
        improvement.ai_used
          ? "AI suggestions ready"
          : "AI is offline — showing checklist suggestions",
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to improve resume"));
    } finally {
      setBusyId(null);
    }
  };

  const handleDeleteResume = async (id: string) => {
    try {
      setBusyId(id);
      await careerToolsApi.deleteResume(id);
      await refreshResumes();
      toast.success("Resume deleted");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to delete resume"));
    } finally {
      setBusyId(null);
    }
  };

  const handleCreatePortfolio = async () => {
    if (!newPortfolioTitle.trim()) return;
    try {
      setCreatingPortfolio(true);
      await careerToolsApi.createPortfolio({ title: newPortfolioTitle.trim() });
      setNewPortfolioTitle("");
      await refreshPortfolios();
      toast.success("Portfolio created");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create portfolio"));
    } finally {
      setCreatingPortfolio(false);
    }
  };

  const handlePublish = async (id: string) => {
    try {
      setBusyId(id);
      const result = await careerToolsApi.publishPortfolio(id);
      await refreshPortfolios();
      toast.success(`Published at ${result.public_url}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to publish portfolio"));
    } finally {
      setBusyId(null);
    }
  };

  const handleDeletePortfolio = async (id: string) => {
    try {
      setBusyId(id);
      await careerToolsApi.deletePortfolio(id);
      await refreshPortfolios();
      toast.success("Portfolio deleted");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to delete portfolio"));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <PageShell
      description="Build resumes and portfolios, then run an offline ATS check to see how applicant tracking systems will score your CV."
      eyebrow="Career Tools"
      title="Resumes & portfolios"
    >
      {loading ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <>
          <section className="space-y-4">
            <SectionHeader description="Manage your CVs and check them against ATS heuristics." eyebrow="Resumes" title="Your resumes" />

            <div className="flex flex-wrap gap-2">
              <button
                className={cn(
                  "transition-smooth rounded-full border px-4 py-2 text-sm font-medium",
                  resumeMode === "upload"
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/70 text-muted-foreground hover:border-primary/40",
                )}
                onClick={() => setResumeMode("upload")}
                type="button"
              >
                Upload CV
              </button>
              <button
                className={cn(
                  "transition-smooth rounded-full border px-4 py-2 text-sm font-medium",
                  resumeMode === "create"
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/70 text-muted-foreground hover:border-primary/40",
                )}
                onClick={() => setResumeMode("create")}
                type="button"
              >
                Create new
              </button>
            </div>

            {resumeMode === "create" ? (
              <form
                className="atlas-panel flex flex-col gap-3 p-4 sm:flex-row"
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleCreateResume();
                }}
              >
                <Input
                  onChange={(event) => setNewResumeTitle(event.target.value)}
                  placeholder="New resume title (e.g. Backend Engineer CV)"
                  value={newResumeTitle}
                />
                <Button className="gradient-primary shrink-0" disabled={creatingResume} type="submit">
                  {creatingResume ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                  New resume
                </Button>
              </form>
            ) : (
              <div className="atlas-panel flex flex-col items-start gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium">Upload your CV</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    PDF, DOCX, or TXT up to 5 MB. We extract contact info, experience, and skills, then score it for ATS.
                  </p>
                </div>
                <input
                  accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  className="hidden"
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  type="file"
                />
                <Button
                  className="gradient-primary shrink-0"
                  disabled={uploading}
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
                  Choose file
                </Button>
              </div>
            )}

            {resumes.length === 0 ? (
              <StatePanel
                description="Upload a PDF/DOCX/TXT CV or create a blank resume to start tracking ATS readiness."
                state="empty"
                title="No resumes yet"
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {resumes.map((resume) => (
                  <ResumeCard
                    ats={atsResults[resume.id]}
                    busy={busyId === resume.id}
                    improvement={improvements[resume.id]}
                    key={resume.id}
                    onDelete={() => void handleDeleteResume(resume.id)}
                    onImprove={() => void handleImprove(resume.id)}
                    resume={resume}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <SectionHeader description="Showcase your projects with a shareable public page." eyebrow="Portfolios" title="Your portfolios" />

            <form
              className="atlas-panel flex flex-col gap-3 p-4 sm:flex-row"
              onSubmit={(event) => {
                event.preventDefault();
                void handleCreatePortfolio();
              }}
            >
              <Input
                onChange={(event) => setNewPortfolioTitle(event.target.value)}
                placeholder="New portfolio title (e.g. My Data Projects)"
                value={newPortfolioTitle}
              />
              <Button className="gradient-primary shrink-0" disabled={creatingPortfolio} type="submit">
                {creatingPortfolio ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                New portfolio
              </Button>
            </form>

            {portfolios.length === 0 ? (
              <StatePanel
                description="Create a portfolio to publish a public showcase of your work."
                state="empty"
                title="No portfolios yet"
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {portfolios.map((portfolio) => (
                  <PortfolioCard
                    deleting={busyId === portfolio.id}
                    key={portfolio.id}
                    onDelete={() => void handleDeletePortfolio(portfolio.id)}
                    onPublish={() => void handlePublish(portfolio.id)}
                    portfolio={portfolio}
                    publishing={busyId === portfolio.id}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </PageShell>
  );
};

export default CareerToolsPage;
