import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { type SavedJob, getApiErrorMessage, jobApi } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

export default function SavedJobsPage() {
  const { toast } = useToast();
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSavedJobs = async () => {
      try {
        setLoading(true);
        setSavedJobs(await jobApi.getSavedJobs());
      } catch (error) {
        toast({
          title: "Error",
          description: getApiErrorMessage(error, "Failed to load saved jobs"),
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    void fetchSavedJobs();
  }, [toast]);

  const handleRemove = async (savedJobId: string) => {
    try {
      await jobApi.unsaveJob(savedJobId);
      setSavedJobs((previous) => previous.filter((item) => item.id !== savedJobId));
    } catch (error) {
      toast({
        title: "Error",
        description: getApiErrorMessage(error, "Failed to remove saved job"),
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <PageShell
      actions={
        <Button asChild variant="outline">
          <Link to={ROUTES.jobs}>Back to jobs</Link>
        </Button>
      }
      description="Your saved jobs should stay easy to revisit and compare."
      eyebrow="Saved jobs"
      title="Bookmarked opportunities"
    >
      {savedJobs.length > 0 ? (
        <div className="space-y-4">
          {savedJobs.map((savedItem) => (
            <div className="atlas-panel p-5" key={savedItem.id}>
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <h2 className="text-2xl font-bold">{savedItem.job.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {savedItem.job.company_name} • {savedItem.job.location}
                  </p>
                  <p className="mt-3 text-sm text-muted-foreground">
                    Saved on {new Date(savedItem.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button asChild variant="outline">
                    <Link to={ROUTES.jobDetail(savedItem.job.id)}>View detail</Link>
                  </Button>
                  <Button onClick={() => handleRemove(savedItem.id)} variant="destructive">
                    Remove
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <StatePanel
          action={
            <Button asChild className="gradient-primary">
              <Link to={ROUTES.jobs}>Browse jobs</Link>
            </Button>
          }
          description="Save jobs from the discovery surface to compare them later."
          state="empty"
          title="No saved jobs yet"
        />
      )}
    </PageShell>
  );
}
