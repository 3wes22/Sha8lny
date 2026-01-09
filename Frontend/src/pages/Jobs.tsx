import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  MapPin,
  Briefcase,
  Clock,
  Bookmark,
  ExternalLink,
  TrendingUp,
  Filter,
  Info,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  type: "Full-time" | "Part-time" | "Contract" | "Internship";
  level: "Junior" | "Mid-level" | "Senior";
  postedAgo: string;
  matchPercentage: number;
  tags: string[];
  recommended?: boolean;
};

const SAVED_JOBS_STORAGE_KEY = "sha8alny_saved_jobs";

const ALL_JOBS: Job[] = [
  {
    id: 1,
    title: "Full Stack Developer",
    company: "Tech Vision",
    location: "Cairo, Egypt",
    type: "Full-time",
    level: "Mid-level",
    postedAgo: "2 days ago",
    matchPercentage: 92,
    tags: ["React", "Node.js", "REST APIs", "PostgreSQL"],
    recommended: true,
  },
  {
    id: 2,
    title: "Frontend Developer (React)",
    company: "Creative Labs",
    location: "Remote",
    type: "Full-time",
    level: "Junior",
    postedAgo: "5 days ago",
    matchPercentage: 88,
    tags: ["React", "TypeScript", "Tailwind CSS"],
    recommended: true,
  },
  {
    id: 3,
    title: "Backend Engineer (Node.js)",
    company: "Cloud Systems",
    location: "Cairo, Egypt",
    type: "Full-time",
    level: "Mid-level",
    postedAgo: "1 day ago",
    matchPercentage: 84,
    tags: ["Node.js", "Express", "MongoDB", "Redis"],
    recommended: true,
  },
  {
    id: 4,
    title: "Software Engineer",
    company: "Startup Hub",
    location: "Remote",
    type: "Full-time",
    level: "Junior",
    postedAgo: "4 days ago",
    matchPercentage: 79,
    tags: ["JavaScript", "React", "APIs"],
  },
  {
    id: 5,
    title: "Junior Web Developer",
    company: "Digital Studio",
    location: "Alexandria, Egypt",
    type: "Part-time",
    level: "Junior",
    postedAgo: "3 days ago",
    matchPercentage: 73,
    tags: ["HTML", "CSS", "JavaScript"],
  },
  {
    id: 6,
    title: "DevOps Engineer",
    company: "InfraWorks",
    location: "Cairo, Egypt",
    type: "Full-time",
    level: "Senior",
    postedAgo: "1 week ago",
    matchPercentage: 68,
    tags: ["AWS", "Docker", "CI/CD"],
  },
  {
    id: 7,
    title: "Intern Software Engineer",
    company: "Future Tech",
    location: "Cairo, Egypt",
    type: "Internship",
    level: "Junior",
    postedAgo: "2 weeks ago",
    matchPercentage: 71,
    tags: ["JavaScript", "Git", "Problem Solving"],
  },
];

// 🧠 Mock assessment result used for "Why this job?"
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
    // basic validation
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

  const headline = `Matches your ${MOCK_ASSESSMENT.level.toLowerCase()} ${MOCK_ASSESSMENT.targetPath} profile`;

  const bullets: string[] = [];

  bullets.push(
    `You selected ${MOCK_ASSESSMENT.targetPath} as your target path in your latest assessment. This role is explicitly looking for a ${job.title}.`
  );

  if (matchedSkills.length) {
    bullets.push(
      `This job uses key skills you rated strongly in: ${matchedSkills.join(", ")}.`
    );
  } else {
    bullets.push(
      `This job uses technologies related to your current skill set (${MOCK_ASSESSMENT.topSkills.join(
        ", "
      )}).`
    );
  }

  bullets.push(
    `Your match score of ${job.matchPercentage}% reflects the overlap between your skills and this job's requirements.`
  );

  if (locationMatch) {
    bullets.push(
      `The location (${job.location}) matches your preferred regions from the assessment.`
    );
  }

  bullets.push(
    `Based on your focus areas (${MOCK_ASSESSMENT.focusAreas.join(
      ", "
    )}), this role can help you grow toward more advanced ${MOCK_ASSESSMENT.targetPath} responsibilities.`
  );

  return { headline, bullets };
};

export default function Jobs() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [locationFilter, setLocationFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [levelFilter, setLevelFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("match-desc");
  const [savedJobs, setSavedJobs] = useState<Job[]>(() => loadSavedJobs());
  const [expandedWhyId, setExpandedWhyId] = useState<number | null>(null);

  useEffect(() => {
    persistSavedJobs(savedJobs);
  }, [savedJobs]);

  const isSaved = (job: Job) => savedJobs.some((j) => j.id === job.id);

  const handleToggleSave = (job: Job) => {
    setSavedJobs((prev) => {
      const exists = prev.some((j) => j.id === job.id);
      const next = exists ? prev.filter((j) => j.id !== job.id) : [...prev, job];

      toast({
        title: exists ? "Removed from saved" : "Saved job",
        description: exists
          ? "This job has been removed from your saved list."
          : "You can find this job later in your Saved Jobs.",
      });

      return next;
    });
  };

  const handleToggleWhy = (jobId: number) => {
    setExpandedWhyId((prev) => (prev === jobId ? null : jobId));
  };

  const filteredJobs = useMemo(() => {
    return ALL_JOBS.filter((job) => {
      const q = searchQuery.toLowerCase().trim();
      if (q) {
        const inText =
          job.title.toLowerCase().includes(q) ||
          job.company.toLowerCase().includes(q) ||
          job.tags.some((tag) => tag.toLowerCase().includes(q));
        if (!inText) return false;
      }

      if (locationFilter !== "all") {
        if (locationFilter === "cairo" && !job.location.includes("Cairo")) return false;
        if (locationFilter === "alexandria" && !job.location.includes("Alexandria"))
          return false;
        if (locationFilter === "remote" && job.location !== "Remote") return false;
      }

      if (typeFilter !== "all" && job.type.toLowerCase() !== typeFilter) return false;
      if (levelFilter !== "all" && job.level.toLowerCase() !== levelFilter) return false;

      return true;
    }).sort((a, b) => {
      if (sortOrder === "match-desc") return b.matchPercentage - a.matchPercentage;
      if (sortOrder === "match-asc") return a.matchPercentage - b.matchPercentage;
      if (sortOrder === "recent") return a.id < b.id ? 1 : -1; // mock recency
      return 0;
    });
  }, [searchQuery, locationFilter, typeFilter, levelFilter, sortOrder]);

  const recommendedJobs = filteredJobs.filter((job) => job.recommended);
  const otherJobs = filteredJobs.filter((job) => !job.recommended);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl gradient-primary mb-3">
            <Briefcase className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            Job Recommendations
          </h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            Opportunities tailored to your skills, preferences, and recent assessment
            results. Save interesting roles and review them any time.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
            onClick={() => navigate("/jobs/saved")}
          >
            <Bookmark className="h-4 w-4" />
            View Saved Jobs
          </Button>
          <Badge variant="outline" className="text-xs">
            <TrendingUp className="h-3 w-3 mr-1" />
            Based on your latest assessment
          </Badge>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center justify-between">
            <span>Search & Filters</span>
            <Badge variant="outline" className="text-xs">
              <Filter className="h-3 w-3 mr-1" />
              Refine results
            </Badge>
          </CardTitle>
          <CardDescription>
            Narrow down roles by title, location, experience level, and employment type.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* Search */}
            <div className="md:col-span-5">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs by title, company, or skill..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {/* Location */}
            <div className="md:col-span-3">
              <Select
                value={locationFilter}
                onValueChange={(value) => setLocationFilter(value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Location" />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  <SelectItem value="all">All Locations</SelectItem>
                  <SelectItem value="cairo">Cairo</SelectItem>
                  <SelectItem value="alexandria">Alexandria</SelectItem>
                  <SelectItem value="remote">Remote</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Experience Level */}
            <div className="md:col-span-2">
              <Select value={levelFilter} onValueChange={(value) => setLevelFilter(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Experience" />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="junior">Junior</SelectItem>
                  <SelectItem value="mid-level">Mid-level</SelectItem>
                  <SelectItem value="senior">Senior</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Job Type */}
            <div className="md:col-span-2">
              <Select value={typeFilter} onValueChange={(value) => setTypeFilter(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Job Type" />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="full-time">Full-time</SelectItem>
                  <SelectItem value="part-time">Part-time</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="internship">Internship</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort by */}
            <div className="md:col-span-2">
              <Select value={sortOrder} onValueChange={(value) => setSortOrder(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  <SelectItem value="match-desc">Match: High to Low</SelectItem>
                  <SelectItem value="match-asc">Match: Low to High</SelectItem>
                  <SelectItem value="recent">Most Recent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommended for you */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Recommended for You
          </h2>
          <p className="text-xs text-muted-foreground">
            Based on your assessment results, profile, and saved preferences.
          </p>
        </div>

        {recommendedJobs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No recommendations match your current filters. Try clearing some filters or
            searching with a different keyword.
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendedJobs.map((job) => {
            const saved = isSaved(job);
            const why = getWhyThisJobText(job);
            const isExpanded = expandedWhyId === job.id;

            return (
              <Card key={job.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Link to={`/jobs/${job.id}`}>
                          <CardTitle className="text-lg md:text-xl hover:text-primary transition-smooth cursor-pointer">
                            {job.title}
                          </CardTitle>
                        </Link>
                        <Badge className="bg-success/10 text-success border-success">
                          {job.matchPercentage}% Match
                        </Badge>
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
                      className={saved ? "text-accent" : ""}
                      onClick={() => handleToggleSave(job)}
                      aria-label={saved ? "Remove from saved" : "Save job"}
                    >
                      <Bookmark className={`h-5 w-5 ${saved ? "fill-current" : ""}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col gap-3">
                  <div className="flex flex-wrap gap-2">
                    {job.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  {isExpanded && (
                    <div className="mt-1 rounded-md border bg-muted/40 p-3 text-xs md:text-sm">
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

                  <div className="mt-auto flex items-center justify-between pt-2 border-t">
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

      {/* All jobs */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-xl font-semibold">All Jobs</h2>
          <p className="text-xs text-muted-foreground">
            Browse all roles that match your filters.
          </p>
        </div>

        {otherJobs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No jobs found. Try adjusting your search or filters.
          </p>
        )}

        <div className="space-y-4">
          {otherJobs.map((job) => {
            const saved = isSaved(job);
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
                        <Badge variant="outline">
                          {job.matchPercentage}% Match
                        </Badge>
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
                      className={saved ? "text-accent" : ""}
                      onClick={() => handleToggleSave(job)}
                      aria-label={saved ? "Remove from saved" : "Save job"}
                    >
                      <Bookmark className={`h-5 w-5 ${saved ? "fill-current" : ""}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {job.tags.map((tag) => (
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

      {/* Pagination placeholder */}
      <div className="flex items-center justify-center gap-2">
        <Button variant="outline" disabled>
          Previous
        </Button>
        <Button variant="outline" className="bg-primary text-primary-foreground">
          1
        </Button>
        <Button variant="outline">2</Button>
        <Button variant="outline">3</Button>
        <Button variant="outline">Next</Button>
      </div>
    </div>
  );
}
