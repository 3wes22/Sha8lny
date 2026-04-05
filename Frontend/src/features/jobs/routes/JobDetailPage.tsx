import { useEffect, useState } from "react";
import { ArrowLeft, ExternalLink, Loader2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type Job, getApiErrorMessage, jobApi } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { toast } from "sonner";

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadJob = async () => {
      if (!jobId) return;

      try {
        setLoading(true);
        setJob(await jobApi.get(jobId));
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to load job details"));
      } finally {
        setLoading(false);
      }
    };

    void loadJob();
  }, [jobId]);

  const toggleSave = async () => {
    if (!job) return;

    try {
      const response = await jobApi.toggleSaveJob(job.id);
      setJob({ ...job, is_saved: response.is_saved });
      toast.success(response.detail);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update saved state"));
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!job) {
    return (
      <StatePanel
        description="The requested job could not be loaded."
        state="error"
        title="Job unavailable"
      />
    );
  }

  return (
    <PageShell
      actions={
        <Button asChild variant="outline">
          <Link to={ROUTES.jobs}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to jobs
          </Link>
        </Button>
      }
      description="Inspect the role with enough detail to decide whether to save, apply, or move on."
      eyebrow="Job detail"
      title={job.title}
      aside={
        <div className="space-y-4">
          <div className="atlas-panel p-5">
            <p className="type-kicker">Company</p>
            <p className="mt-3 text-xl font-bold">{job.company_name}</p>
            <p className="mt-2 text-sm text-muted-foreground">{job.location}</p>
          </div>
          <div className="atlas-panel p-5">
            <p className="type-kicker">Actions</p>
            <div className="mt-4 grid gap-3">
              <Button onClick={toggleSave} variant="outline">
                {job.is_saved ? "Saved" : "Save role"}
              </Button>
              {job.external_action_available ? (
                <Button asChild className="gradient-primary">
                  <a href={job.external_url} rel="noreferrer" target="_blank">
                    Apply externally
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              ) : (
                <Button disabled>Apply link unavailable</Button>
              )}
            </div>
          </div>
        </div>
      }
    >
      <div className="atlas-panel p-6">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{job.job_type}</Badge>
          <Badge variant="outline">{job.experience_level}</Badge>
          {job.is_remote ? <Badge variant="secondary">Remote</Badge> : null}
        </div>
        <div className="mt-6 space-y-6">
          <section>
            <h2 className="text-2xl font-bold">Description</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">
              {job.description || "No description provided."}
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold">Requirements</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">
              {job.requirements || "No requirements provided."}
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold">Responsibilities</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">
              {job.responsibilities || "No responsibilities provided."}
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-bold">Skills</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {job.skills.map((skill) => (
                <Badge key={skill.id} variant={skill.is_required ? "default" : "outline"}>
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
          </section>
        </div>
      </div>
    </PageShell>
  );
}
