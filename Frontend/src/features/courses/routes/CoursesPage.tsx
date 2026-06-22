import React, { useCallback, useEffect, useState } from "react";
import { BookOpen, ExternalLink, Loader2, Search, Star } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { cn } from "@/lib/utils";
import {
  courseApi,
  getApiErrorMessage,
  type CourseLevel,
  type CourseListItem,
  type CoursePlatform,
} from "@/lib/api";

const DIFFICULTY_FILTERS: { label: string; value: CourseLevel | "all" }[] = [
  { label: "All levels", value: "all" },
  { label: "Beginner", value: "beginner" },
  { label: "Intermediate", value: "intermediate" },
  { label: "Advanced", value: "advanced" },
];

const formatPrice = (price: CourseListItem["price"], currency: string) => {
  const value = Number(price);
  if (!value) return "Free";
  return `${currency} ${value.toFixed(0)}`;
};

const CourseCard: React.FC<{ course: CourseListItem }> = ({ course }) => {
  const [opening, setOpening] = useState(false);

  const openCourse = async () => {
    try {
      setOpening(true);
      const full = await courseApi.get(course.id);
      if (full.course_url) {
        window.open(full.course_url, "_blank", "noopener,noreferrer");
      } else {
        toast.error("This course has no external link yet.");
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to open course"));
    } finally {
      setOpening(false);
    }
  };

  return (
    <div className="panel-paper card-elevated flex flex-col gap-3 rounded-[1.5rem] p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="rounded-2xl bg-background/80 p-3">
          <BookOpen className="h-5 w-5 text-primary" />
        </div>
        <span className="type-kicker text-[0.65rem]">{course.level?.replace("_", " ")}</span>
      </div>
      <div>
        <h3 className="text-lg font-semibold leading-tight">{course.title}</h3>
        {course.platform_name ? (
          <p className="mt-1 text-sm text-muted-foreground">{course.platform_name}</p>
        ) : null}
      </div>
      <div className="mt-auto flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {Number(course.rating) > 0 ? (
            <span className="inline-flex items-center gap-1">
              <Star className="h-4 w-4 fill-warning text-warning" />
              {Number(course.rating).toFixed(1)}
            </span>
          ) : null}
          <span className="font-semibold text-foreground">
            {formatPrice(course.price, course.currency)}
          </span>
        </div>
        <Button disabled={opening} onClick={openCourse} size="sm" variant="outline">
          {opening ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
          <span className="ml-1">View</span>
        </Button>
      </div>
    </div>
  );
};

const CoursesPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState<CourseLevel | "all">("all");
  const [freeOnly, setFreeOnly] = useState(false);
  const [platform, setPlatform] = useState<string>("");
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [platforms, setPlatforms] = useState<CoursePlatform[]>([]);
  const [loading, setLoading] = useState(true);

  const runSearch = useCallback(
    async (overrides: Record<string, unknown> = {}) => {
      const params: Record<string, unknown> = {
        query: query || undefined,
        difficulty: difficulty === "all" ? undefined : difficulty,
        is_free: freeOnly || undefined,
        platform: platform || undefined,
        ...overrides,
      };
      Object.keys(params).forEach((key) => params[key] === undefined && delete params[key]);

      try {
        setLoading(true);
        const response = await courseApi.search(params);
        setCourses(response.results ?? []);
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to load courses"));
      } finally {
        setLoading(false);
      }
    },
    [query, difficulty, freeOnly, platform],
  );

  useEffect(() => {
    courseApi
      .platforms()
      .then((response) => setPlatforms(response.results ?? []))
      .catch(() => setPlatforms([]));
    void runSearch();
    // Run once on mount; subsequent searches are triggered by user actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDifficulty = (value: CourseLevel | "all") => {
    setDifficulty(value);
    void runSearch({ difficulty: value === "all" ? undefined : value });
  };

  const handleFreeToggle = () => {
    const next = !freeOnly;
    setFreeOnly(next);
    void runSearch({ is_free: next || undefined });
  };

  const handlePlatform = (value: string) => {
    setPlatform(value);
    void runSearch({ platform: value || undefined });
  };

  return (
    <PageShell
      description="Browse and search courses aggregated across learning platforms. Filter by level, price, and provider."
      eyebrow="Courses"
      title="Course catalog"
    >
      <form
        className="atlas-panel flex flex-col gap-4 p-5"
        onSubmit={(event) => {
          event.preventDefault();
          void runSearch({ query: query || undefined });
        }}
      >
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search courses, topics, or instructors"
              value={query}
            />
          </div>
          <Button className="gradient-primary" type="submit">
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {DIFFICULTY_FILTERS.map((filter) => (
            <button
              className={cn(
                "transition-smooth rounded-full border px-3 py-1.5 text-sm",
                difficulty === filter.value
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border/70 text-muted-foreground hover:border-primary/40",
              )}
              key={filter.value}
              onClick={() => handleDifficulty(filter.value)}
              type="button"
            >
              {filter.label}
            </button>
          ))}

          <span className="mx-1 h-5 w-px bg-border" />

          <button
            className={cn(
              "transition-smooth rounded-full border px-3 py-1.5 text-sm",
              freeOnly
                ? "border-success bg-success/10 text-success"
                : "border-border/70 text-muted-foreground hover:border-primary/40",
            )}
            onClick={handleFreeToggle}
            type="button"
          >
            Free only
          </button>

          {platforms.length > 0 ? (
            <select
              className="focus-ring rounded-full border border-border/70 bg-background px-3 py-1.5 text-sm text-muted-foreground"
              onChange={(event) => handlePlatform(event.target.value)}
              value={platform}
            >
              <option value="">All platforms</option>
              {platforms.map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
          ) : null}
        </div>
      </form>

      {loading ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : courses.length === 0 ? (
        <StatePanel
          description="No courses match these filters yet. Try a broader search or clear the filters."
          state="empty"
          title="No courses found"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {courses.map((course) => (
            <CourseCard course={course} key={course.id} />
          ))}
        </div>
      )}
    </PageShell>
  );
};

export default CoursesPage;
