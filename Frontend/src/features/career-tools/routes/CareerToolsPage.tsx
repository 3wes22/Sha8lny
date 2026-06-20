import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  FileText,
  Globe,
  Loader2,
  Lock,
  Plus,
  Sparkles,
  Trash2,
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

const ResumeCard: React.FC<{
  resume: ResumeListItem;
  ats?: AtsResult;
  optimizing: boolean;
  deleting: boolean;
  onOptimize: () => void;
  onDelete: () => void;
}> = ({ resume, ats, optimizing, deleting, onOptimize, onDelete }) => {
  const score = ats ? ats.ats_score : Number(resume.ats_score);
  const grade = ats ? ats.ats_grade : resume.ats_grade;

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

      {ats?.suggestions?.length ? (
        <ul className="space-y-1.5 rounded-2xl bg-background/60 p-3 text-sm">
          {ats.suggestions.map((suggestion) => (
            <li className="flex items-start gap-2 text-muted-foreground" key={suggestion}>
              <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
              {suggestion}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="flex items-center gap-2">
        <Button className="flex-1" disabled={optimizing} onClick={onOptimize} size="sm" variant="outline">
          {optimizing ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
          Optimize for ATS
        </Button>
        <Button
          aria-label={`Delete ${resume.title}`}
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
  const [busyId, setBusyId] = useState<string | null>(null);
  const [newResumeTitle, setNewResumeTitle] = useState("");
  const [newPortfolioTitle, setNewPortfolioTitle] = useState("");
  const [creatingResume, setCreatingResume] = useState(false);
  const [creatingPortfolio, setCreatingPortfolio] = useState(false);

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

  const handleOptimize = async (id: string) => {
    try {
      setBusyId(id);
      const result = await careerToolsApi.optimizeAts(id);
      setAtsResults((prev) => ({ ...prev, [id]: result }));
      toast.success(`ATS score: ${Math.round(result.ats_score)} (${result.ats_grade})`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to optimize resume"));
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

            {resumes.length === 0 ? (
              <StatePanel
                description="Create your first resume to start tracking ATS readiness."
                state="empty"
                title="No resumes yet"
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {resumes.map((resume) => (
                  <ResumeCard
                    ats={atsResults[resume.id]}
                    deleting={busyId === resume.id}
                    key={resume.id}
                    onDelete={() => void handleDeleteResume(resume.id)}
                    onOptimize={() => void handleOptimize(resume.id)}
                    optimizing={busyId === resume.id}
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
