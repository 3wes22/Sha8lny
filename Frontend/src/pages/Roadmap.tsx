import React from "react";
import { Button } from "@/components/ui/button";
import { Map } from "lucide-react";
import { TrackTreeView } from "@/components/Roadmap/TrackTreeView";

// ✅ All career paths (same idea as Assessment list)
// Later: replace this with data from backend / assessment result
const allTracks = [
  "Frontend",
  "Backend",
  "Full Stack",
  "DevOps",
  "Data Analyst",
  "Data Scientist",
  "Data Engineer",
  "AI Engineer",
  "Machine Learning",
  "Cyber Security",
  "UI/UX Designer",
  "Product Manager",
  "QA",
  "Software Architect",
  "Android",
  "iOS",
  "Blockchain",
  "Technical Writer",
  "MLOps",
];

// ✅ Top recommended tracks (later: from assessment)
const recommendedTracks = ["Frontend", "Backend", "Full Stack"];

const RoadmapPage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Hero / header */}
      <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Career Roadmap
          </h1>
          <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
            A step-by-step learning plan to grow in your chosen career path.
            Track your progress and deep-dive into each track to see exactly what to learn next.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="text-xs md:text-sm">
            View Learning Pace
          </Button>
          <Button size="sm" className="text-xs md:text-sm gradient-primary">
            <Map className="mr-2 h-4 w-4" />
            Download Roadmap
          </Button>
        </div>
      </section>

      {/* ===== Premium Overview ===== */}
      <section className="space-y-5">
        <div className="relative overflow-hidden rounded-2xl border border-subtle shadow-soft-lg">
          {/* soft glow */}
          <div className="pointer-events-none absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-cyan-500/15 blur-3xl" />

          <div className="gradient-soft px-5 py-5 md:px-7 md:py-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Map className="h-4 w-4" />
                  </span>
                  <h2 className="text-base md:text-lg font-semibold">
                    Your Learning Roadmap
                  </h2>
                </div>
                <p className="text-xs md:text-sm text-muted-foreground max-w-2xl">
                  Choose a track and follow a clear step-by-step plan. Click any topic to see videos
                  and learning resources.
                </p>
              </div>

              {/* Stats pills */}
              <div className="flex flex-wrap gap-2">
                <div className="rounded-full border border-subtle bg-card px-3 py-1.5 text-xs">
                  <span className="text-muted-foreground">Tracks:</span>{" "}
                  <span className="font-semibold text-foreground">{allTracks.length}</span>
                </div>
                <div className="rounded-full border border-subtle bg-card px-3 py-1.5 text-xs">
                  <span className="text-muted-foreground">Recommended:</span>{" "}
                  <span className="font-semibold text-foreground">
                    {recommendedTracks.length}
                  </span>
                </div>
                <div className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs text-primary">
                  Personalized learning
                </div>
              </div>
            </div>

            {/* Progress bar (optional visual) */}
            <div className="mt-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Roadmap completion</span>
                <span className="font-medium text-foreground">68%</span>
              </div>

              <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary via-indigo-500 to-cyan-400 transition-all duration-700"
                  style={{ width: "68%" }}
                />
              </div>

              <div className="text-[11px] text-muted-foreground">
                Tip: Try a{" "}
                <span className="font-medium text-foreground">
                  20-minute daily streak
                </span>{" "}
                to build momentum.
              </div>
            </div>
          </div>
        </div>

        {/* ===== Recommended Tracks ===== */}
        <div className="rounded-2xl border border-subtle bg-card p-4 shadow-soft-lg">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold">Recommended Tracks</h3>
              <p className="text-xs text-muted-foreground">
                Pick a track to explore. Recommended tracks will be based on your assessment result later.
              </p>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="text-xs">
                Customize
              </Button>
              <Button size="sm" className="text-xs gradient-primary">
                Continue Learning
              </Button>
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {allTracks.map((name) => {
              const isRecommended = recommendedTracks.includes(name);

              return (
                <button
                  key={name}
                  className={[
                    "rounded-2xl border p-3 text-left transition-smooth",
                    "hover:-translate-y-0.5 hover:shadow-md",
                    isRecommended
                      ? "border-primary/30 bg-primary/5 ring-1 ring-primary/20"
                      : "border-subtle bg-card hover:bg-muted/60",
                  ].join(" ")}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-semibold">{name}</div>
                      <div className="text-[11px] text-muted-foreground">
                        Step-by-step roadmap + videos
                      </div>
                    </div>

                    {isRecommended && (
                      <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[10px] text-primary">
                        Recommended
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* ===== Track Explorer (Tree + Videos) ===== */}
      <TrackTreeView />
    </div>
  );
};

export default RoadmapPage;
