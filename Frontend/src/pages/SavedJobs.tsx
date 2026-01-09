import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Briefcase, Clock, Bookmark, ExternalLink, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Job } from "./Jobs";

const SAVED_JOBS_STORAGE_KEY = "sha8alny_saved_jobs";

// Same mock assessment for "Why this job?"
const MOCK_ASSESSMENT = {
  targetPath: "Full Stack Developer",
  level: "Intermediate",
  topSkills: ["React", "JavaScript", "REST APIs"],
  focusAreas: ["Backend depth", "Production experience"],
  preferredLocations: ["Cairo, Egypt", "Remote"],
};

const loadSavedJobs = (): Job[] => {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(SAVED_JOBS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item: any) => item && typeof item.id === "number" && typeof item.title === "string"
    );
  } catch {
    return [];
  }
};

const persistSavedJobs = (jobs: Job[]) => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SAVED_JOBS_STORAGE_KEY, JSON.stringify(jobs));
  } catch {
    // ignore
  }
};

const getWhyThisJobText = (job: Job) => {
  const locationMatch = MOCK_ASSESSMENT.preferredLocations.includes(job.location);
  const matchedSkills = job.tags.filter((tag) =>
    MOCK_ASSESSMENT.topSkills.includes(tag)
  );

  const headline = `Still aligned with your ${MOCK_ASSESSMENT.level.toLowerCase()} ${MOCK_ASSESSMENT.targetPath} profile`;

  const bullets: string[] = [];

  bullets.push(
    `You saved this ${job.title} role after your last assessment targeting ${MOCK_ASSESSMENT.targetPath}.`
  );

  if (matchedSkills.length) {
    bullets.push(
      `It focuses on skills you rated strongly: ${matchedSkills.join(", ")}.`
    );
  } else {
    bullets.push(
      `Its tech stack is compatible with your current strengths (${MOCK_ASSESSMENT.topSkills.join(
        ", "
      )}).`
    );
  }

  if (typeof job.matchPercentage === "number") {
    bullets.push(
      `Match score: ${job.matchPercentage}% based on your skills and preferences.`
    );
  }

  if (locationMatch) {
    bullets.push(
      `Location (${job.location}) matches your preferred locations from the assessment.`
    );
  }

  bullets.push(
    `It can help you progress on your focus areas: ${MOCK_ASSESSMENT.focusAreas.join(
      ", "
    )}.`
  );

  return { headline, bullets };
};

export default function SavedJobs() {
  const { toast } = useToast();
  const [savedJobs, setSavedJobs] = useState<Job[]>(() => loadSavedJobs());
  const [expandedWhyId, setExpandedWhyId] = useState<number | null>(null);

  useEffect(() => {
    // in case localStorage changed in another tab
    setSavedJobs(loadSavedJobs());
  }, []);

  useEffect(() => {
    persistSavedJobs(savedJobs);
  }, [savedJobs]);

  const handleRemove = (job: Job) => {
    setSavedJobs((prev) => {
      const next = prev.filter((j) => j.id !== job.id);
      toast({
        title: "Removed from saved jobs",
        description: "You can always find new recommendations on the Jobs page.",
      });
      return next;
    });
  };

  const handleToggleWhy = (jobId: number) => {
    setExpandedWhyId((prev) => (prev === jobId ? null : jobId));
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-muted mb-3">
            <Bookmark className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-bold">Saved Jobs</h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            Review and compare the jobs you&apos;ve saved from your recommendations.
            Use the &quot;Why this job?&quot; section to check how each role fits your
            assessment profile.
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/jobs">Back to Job Recommendations</Link>
        </Button>
      </div>

      {savedJobs.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No saved jobs yet</CardTitle>
            <CardDescription>
              Save jobs from the recommendations page to see them listed here.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between gap-4">
            <div className="text-sm text-muted-foreground">
              Start from your personalized job recommendations and bookmark roles that
              interest you.
            </div>
            <Button asChild className="gradient-primary">
              <Link to="/jobs">Browse Jobs</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xl font-semibold">
              You have {savedJobs.length} saved job
              {savedJobs.length > 1 ? "s" : ""}
            </h2>
            <p className="text-xs text-muted-foreground">
              Saved jobs are stored locally in your browser for this account/demo.
            </p>
          </div>

          <div className="space-y-4">
            {savedJobs.map((job) => {
              const why = getWhyThisJobText(job);
              const isExpanded = expandedWhyId === job.id;

              return (
                <Card key={job.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Link to={`/jobs/${job.id}`}>
                            <CardTitle className="text-lg md:text-xl hover:text-primary transition-smooth cursor-pointer">
                              {job.title}
                            </CardTitle>
                          </Link>
                          {typeof job.matchPercentage === "number" && (
                            <Badge className="bg-success/10 text-success border-success">
                              {job.matchPercentage}% Match
                            </Badge>
                          )}
                        </div>
                        <CardDescription className="flex items-center gap-4 flex-wrap">
                          <span className="font-medium text-foreground">
                            {job.company}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {job.location}
                          </span>
                          <span className="flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            {job.type}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {job.postedAgo}
                          </span>
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemove(job)}
                        aria-label="Remove saved job"
                      >
                        <Bookmark className="h-5 w-5" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {job.tags?.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    {isExpanded && (
                      <div className="rounded-md border bg-muted/40 p-3 text-xs md:text-sm">
                        <p className="font-medium mb-1">Why this job?</p>
                        <p className="text-xs text-muted-foreground mb-1">
                          {why.headline}
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                          {why.bullets.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs"
                          onClick={() => handleToggleWhy(job.id)}
                        >
                          <Info className="h-3 w-3 mr-1" />
                          {isExpanded ? "Hide reason" : "Why this job?"}
                        </Button>
                      </div>
                      <div className="flex gap-2">
                        <Link to={`/jobs/${job.id}`}>
                          <Button variant="outline" size="sm">
                            View Details
                          </Button>
                        </Link>
                        <Button size="sm" className="gradient-primary">
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Apply Now
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
