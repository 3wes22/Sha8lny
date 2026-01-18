import { useEffect, useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
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
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Loader2,
  Filter,
  Building2,
  DollarSign,
  Calendar,
} from "lucide-react";
import { toast } from "sonner";
import { jobApi, type JobListItem, type JobSearchParams } from "@/lib/api";

const SAVED_JOBS_KEY = "sha8alny_saved_jobs";

// Utility functions extracted outside component
const formatSalary = (job: JobListItem): string => {
  if (!job.salary_min && !job.salary_max) {
    return "Salary not disclosed";
  }

  const currency = job.salary_currency || "EGP";
  const min = job.salary_min ? parseFloat(job.salary_min).toLocaleString() : null;
  const max = job.salary_max ? parseFloat(job.salary_max).toLocaleString() : null;

  if (min && max) {
    return `${currency} ${min} - ${max}`;
  } else if (min) {
    return `${currency} ${min}+`;
  } else {
    return `Up to ${currency} ${max}`;
  }
};

const formatJobType = (type: string): string => {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const formatExperienceLevel = (level: string): string => {
  const levels: Record<string, string> = {
    entry: "Entry Level",
    mid: "Mid Level",
    senior: "Senior Level",
    lead: "Lead/Manager",
    executive: "Executive",
  };
  return levels[level] || level;
};

const formatPostedDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
};

export default function Jobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [totalCount, setTotalCount] = useState(0);

  // Search filters
  const [searchQuery, setSearchQuery] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [isRemote, setIsRemote] = useState<string>("");

  const loadSavedJobs = useCallback(async () => {
    try {
      const savedJobs = await jobApi.getSavedJobs();
      // Extract job IDs from saved jobs
      const jobIds = new Set(savedJobs.map(item => item.job.id));
      setSavedJobIds(jobIds);
    } catch (error) {
      console.error("Error loading saved jobs:", error);
      // Fallback to empty set if error
      setSavedJobIds(new Set());
    }
  }, []);

  const fetchJobs = useCallback(async (searchParams?: JobSearchParams) => {
    try {
      setSearching(true);
      const response = await jobApi.search(searchParams || {});
      setJobs(response.results);
      setTotalCount(response.count);
    } catch (error: any) {
      console.error("Error fetching jobs:", error);
      toast.error(error?.response?.data?.detail || "Failed to load jobs");
    } finally {
      setLoading(false);
      setSearching(false);
    }
  }, []);

  const handleSearch = useCallback(() => {
    const params: JobSearchParams = {};

    if (searchQuery.trim()) params.query = searchQuery.trim();
    if (location.trim()) params.location = location.trim();
    if (jobType) params.job_type = jobType;
    if (experienceLevel) params.experience_level = experienceLevel;
    if (isRemote === "true") params.is_remote = "true";
    if (isRemote === "false") params.is_remote = "false";

    fetchJobs(params);
  }, [searchQuery, location, jobType, experienceLevel, isRemote, fetchJobs]);

  const handleClearFilters = useCallback(() => {
    setSearchQuery("");
    setLocation("");
    setJobType("");
    setExperienceLevel("");
    setIsRemote("");
    fetchJobs();
  }, [fetchJobs]);

  const toggleSaveJob = useCallback(async (jobId: string) => {
    try {
      const response = await jobApi.toggleSaveJob(jobId);

      if (response.is_saved) {
        setSavedJobIds(prev => new Set([...prev, jobId]));
        toast.success("Job saved successfully");
      } else {
        setSavedJobIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });
        toast.success("Job removed from saved");
      }
    } catch (error: any) {
      console.error("Error toggling saved job:", error);
      toast.error(error?.response?.data?.detail || "Failed to update saved job");
    }
  }, []);

  useEffect(() => {
    loadSavedJobs();
    fetchJobs();
  }, [loadSavedJobs, fetchJobs]);

  const hasActiveFilters = useMemo(
    () => searchQuery || location || jobType || experienceLevel || isRemote,
    [searchQuery, location, jobType, experienceLevel, isRemote]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold mb-2">Find Your Next Opportunity</h1>
          <p className="text-muted-foreground text-lg">
            Explore {totalCount} job openings from top Egyptian companies
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate("/saved-jobs")}
          className="flex items-center gap-2"
        >
          <BookmarkCheck className="h-4 w-4" />
          Saved Jobs ({savedJobIds.size})
        </Button>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Search & Filter Jobs
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by job title, company, or keywords..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Location (e.g., Cairo, Remote)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
            </div>
          </div>

          {/* Filters Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Select value={jobType} onValueChange={setJobType}>
              <SelectTrigger>
                <SelectValue placeholder="Job Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="full_time">Full Time</SelectItem>
                <SelectItem value="part_time">Part Time</SelectItem>
                <SelectItem value="contract">Contract</SelectItem>
                <SelectItem value="internship">Internship</SelectItem>
                <SelectItem value="freelance">Freelance</SelectItem>
              </SelectContent>
            </Select>

            <Select value={experienceLevel} onValueChange={setExperienceLevel}>
              <SelectTrigger>
                <SelectValue placeholder="Experience Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="entry">Entry Level</SelectItem>
                <SelectItem value="mid">Mid Level</SelectItem>
                <SelectItem value="senior">Senior Level</SelectItem>
                <SelectItem value="lead">Lead/Manager</SelectItem>
                <SelectItem value="executive">Executive</SelectItem>
              </SelectContent>
            </Select>

            <Select value={isRemote} onValueChange={setIsRemote}>
              <SelectTrigger>
                <SelectValue placeholder="Work Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">Remote</SelectItem>
                <SelectItem value="false">On-Site</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex gap-2">
              <Button onClick={handleSearch} disabled={searching} className="flex-1">
                {searching ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Search className="h-4 w-4 mr-2" />
                )}
                Search
              </Button>
              {hasActiveFilters && (
                <Button variant="outline" onClick={handleClearFilters}>
                  Clear
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Count */}
      {hasActiveFilters && (
        <div className="text-sm text-muted-foreground">
          Found {jobs.length} job{jobs.length !== 1 ? "s" : ""} matching your criteria
        </div>
      )}

      {/* Job Listings */}
      {jobs.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <div className="mx-auto h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                <Briefcase className="h-8 w-8 text-muted-foreground" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">No jobs found</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  {hasActiveFilters
                    ? "Try adjusting your filters or search criteria"
                    : "Check back later for new opportunities"}
                </p>
              </div>
              {hasActiveFilters && (
                <Button variant="outline" onClick={handleClearFilters}>
                  Clear All Filters
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {jobs.map((job) => {
            const isSaved = savedJobIds.has(job.id);

            return (
              <Card
                key={job.id}
                className="transition-all hover:shadow-lg cursor-pointer group"
              >
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-start gap-3">
                        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <Building2 className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-xl mb-1 group-hover:text-primary transition-colors">
                            {job.title}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium">{job.company_name}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </span>
                            {job.is_remote && (
                              <>
                                <span>•</span>
                                <Badge variant="secondary" className="text-xs">
                                  Remote
                                </Badge>
                              </>
                            )}
                          </CardDescription>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mt-3">
                        <Badge variant="outline">{formatJobType(job.job_type)}</Badge>
                        <Badge variant="outline">
                          {formatExperienceLevel(job.experience_level)}
                        </Badge>
                        {(job.salary_min || job.salary_max) && (
                          <Badge variant="outline" className="flex items-center gap-1">
                            <DollarSign className="h-3 w-3" />
                            {formatSalary(job)}
                          </Badge>
                        )}
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatPostedDate(job.posted_date)}
                        </Badge>
                      </div>
                    </div>

                    <Button
                      variant={isSaved ? "default" : "outline"}
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSaveJob(job.id);
                      }}
                      className="flex-shrink-0"
                    >
                      {isSaved ? (
                        <BookmarkCheck className="h-4 w-4" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => navigate(`/jobs/${job.id}`)}
                      className="flex-1"
                    >
                      View Details
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => window.open(job.external_url || job.platform_name, "_blank")}
                      title="Apply on platform"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Load More - Pagination can be added here */}
      {jobs.length > 0 && jobs.length < totalCount && (
        <div className="text-center py-4">
          <p className="text-sm text-muted-foreground">
            Showing {jobs.length} of {totalCount} jobs
          </p>
        </div>
      )}
    </div>
  );
}
