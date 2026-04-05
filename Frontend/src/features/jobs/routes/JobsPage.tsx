import { useEffect, useState } from "react";
import { Bookmark, Loader2, MapPin, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { jobApi, type JobListItem, type JobSearchParams, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { SectionHeader } from "@/shared/components/SectionHeader";
import { StatePanel } from "@/shared/components/StatePanel";
import { toast } from "sonner";

const formatJobType = (value: string) =>
  value.split("_").map((segment) => `${segment[0].toUpperCase()}${segment.slice(1)}`).join(" ");

export default function JobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [location, setLocation] = useState("");

  const loadSavedJobs = async () => {
    try {
      const savedJobs = await jobApi.getSavedJobs();
      setSavedJobIds(new Set(savedJobs.map((item) => item.job.id)));
    } catch {
      setSavedJobIds(new Set());
    }
  };

  const fetchJobs = async (params: JobSearchParams = {}) => {
    try {
      setSearching(true);
      const response = await jobApi.search(params);
      setJobs(response.results);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to load jobs"));
    } finally {
      setLoading(false);
      setSearching(false);
    }
  };

  useEffect(() => {
    void loadSavedJobs();
    void fetchJobs();
  }, []);

  const handleSearch = () => {
    void fetchJobs({
      query: searchQuery || undefined,
      location: location || undefined,
    });
  };

  const toggleSaveJob = async (jobId: string) => {
    try {
      const response = await jobApi.toggleSaveJob(jobId);
      setSavedJobIds((previous) => {
        const next = new Set(previous);
        if (response.is_saved) next.add(jobId);
        else next.delete(jobId);
        return next;
      });
      toast.success(response.detail);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to update saved job"));
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
        <Button onClick={() => navigate(ROUTES.savedJobs)} variant="outline">
          <Bookmark className="mr-2 h-4 w-4" />
          Saved jobs ({savedJobIds.size})
        </Button>
      }
      description="Explore roles with enough signal to compare them against your current direction."
      eyebrow="Jobs"
      title="Job discovery"
    >
      <div className="atlas-panel p-5">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px_auto]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-10"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search title or company..."
              value={searchQuery}
            />
          </div>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-10"
              onChange={(event) => setLocation(event.target.value)}
              placeholder="Location"
              value={location}
            />
          </div>
          <Button className="gradient-primary" disabled={searching} onClick={handleSearch}>
            {searching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Search
          </Button>
        </div>
      </div>

      <section className="space-y-4">
        <SectionHeader
          description="These results should feel like navigable opportunities, not a generic card grid."
          title={`${jobs.length} roles in view`}
        />

        {jobs.length > 0 ? (
          <div className="space-y-4">
            {jobs.map((job) => (
              <div className="atlas-panel p-5" key={job.id}>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline">{formatJobType(job.job_type)}</Badge>
                      {job.is_remote ? <Badge variant="secondary">Remote</Badge> : null}
                      {job.skill_match_summary ? <Badge variant="outline">{job.skill_match_summary}</Badge> : null}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold">{job.title}</h2>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {job.company_name} • {job.location}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Experience: {job.experience_level} • Posted {new Date(job.posted_date).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button onClick={() => toggleSaveJob(job.id)} variant="outline">
                      {savedJobIds.has(job.id) ? "Saved" : "Save"}
                    </Button>
                    <Button onClick={() => navigate(ROUTES.jobDetail(job.id))}>View role</Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <StatePanel
            description="Try a different title, company, or location filter."
            state="empty"
            title="No jobs found"
          />
        )}
      </section>
    </PageShell>
  );
}
