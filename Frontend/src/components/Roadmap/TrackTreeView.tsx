import React, { useMemo, useState } from "react";
import { TRACKS } from "@/data/tracks";
import type { Track, Stage } from "@/data/tracks";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  Search,
  Sparkles,
  PlayCircle,
  Clock,
  ChevronRight,
  Layers,
} from "lucide-react";

const accentMap: Record<Track["accent"], { ring: string; soft: string; text: string }> = {
  violet: { ring: "ring-primary/30", soft: "bg-primary/10", text: "text-primary" },
  cyan: { ring: "ring-cyan-500/30", soft: "bg-cyan-500/10", text: "text-cyan-600" },
  emerald: { ring: "ring-emerald-500/30", soft: "bg-emerald-500/10", text: "text-emerald-600" },
  amber: { ring: "ring-amber-400/40", soft: "bg-amber-400/10", text: "text-amber-600" },
  rose: { ring: "ring-rose-500/30", soft: "bg-rose-500/10", text: "text-rose-600" },
  blue: { ring: "ring-blue-500/30", soft: "bg-blue-500/10", text: "text-blue-600" },
};

const categoryBadge: Record<Track["category"], string> = {
  Web: "bg-primary/10 text-primary border-primary/20",
  Data: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  AI: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  Mobile: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  Security: "bg-amber-400/10 text-amber-600 border-amber-400/30",
  Product: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  Design: "bg-primary/10 text-primary border-primary/20",
  Engineering: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  DevOps: "bg-amber-400/10 text-amber-600 border-amber-400/30",
  Other: "bg-muted text-foreground border-border",
};

export const TrackTreeView: React.FC = () => {
  const [query, setQuery] = useState("");
  const [activeTrackId, setActiveTrackId] = useState<string>(TRACKS[0]?.id ?? "");
  const [selectedStageId, setSelectedStageId] = useState<string>(TRACKS[0]?.stages?.[0]?.id ?? "");

  const filteredTracks = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return TRACKS;
    return TRACKS.filter((t) => {
      const inTitle = t.label.toLowerCase().includes(q);
      const inDesc = t.description.toLowerCase().includes(q);
      const inCategory = t.category.toLowerCase().includes(q);
      return inTitle || inDesc || inCategory;
    });
  }, [query]);

  const activeTrack: Track | undefined = useMemo(() => {
    return (filteredTracks.find((t) => t.id === activeTrackId) ??
      filteredTracks[0] ??
      TRACKS[0]) as Track | undefined;
  }, [activeTrackId, filteredTracks]);

  const stages: Stage[] = activeTrack?.stages ?? [];

  const selectedStage = useMemo(() => {
    const s = stages.find((x) => x.id === selectedStageId);
    return s ?? stages[0] ?? null;
  }, [selectedStageId, stages]);

  // Keep selection valid when track changes or when search filters tracks
  React.useEffect(() => {
    if (!activeTrack) return;
    setActiveTrackId(activeTrack.id);
    const first = activeTrack.stages?.[0]?.id ?? "";
    if (!activeTrack.stages.some((s) => s.id === selectedStageId)) {
      setSelectedStageId(first);
    }
  }, [activeTrack?.id]);

  const a = activeTrack ? accentMap[activeTrack.accent] : accentMap.violet;

  return (
    <section className="mt-10 space-y-5">
      {/* Header */}
      <div className="rounded-2xl border border-subtle shadow-soft-lg overflow-hidden">
        <div className="px-5 py-5 md:px-7 md:py-6 gradient-soft">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h2 className="text-xl md:text-2xl font-bold tracking-tight">
                Track Explorer
              </h2>
              <p className="text-sm text-muted-foreground max-w-2xl">
                Pick a career track, follow a clean step-by-step roadmap, then click any step to see
                the most important topics and learning videos.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs border ${a.soft} ${a.text}`}>
                <Sparkles className="h-4 w-4" />
                Premium learning flow
              </span>
            </div>
          </div>

          {/* Search */}
          <div className="mt-4 flex items-center gap-2">
            <div className="relative w-full md:max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search tracks (Frontend, DevOps, Data Analyst...)"
                className="pl-9"
              />
            </div>
            <Badge variant="outline" className="hidden md:inline-flex">
              {filteredTracks.length} tracks
            </Badge>
          </div>
        </div>

        {/* Track pills */}
        <div className="px-5 py-4 md:px-7 md:py-5 bg-card">
          <div className="flex flex-wrap gap-2">
            {filteredTracks.map((t) => {
              const isActive = t.id === activeTrackId;
              const acc = accentMap[t.accent];
              return (
                <button
                  key={t.id}
                  onClick={() => {
                    setActiveTrackId(t.id);
                    setSelectedStageId(t.stages?.[0]?.id ?? "");
                  }}
                  className={[
                    "rounded-full border px-4 py-2 text-sm transition-smooth",
                    "hover:bg-muted/70",
                    isActive
                      ? `ring-2 ${acc.ring} ${acc.soft}`
                      : "bg-card",
                  ].join(" ")}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{t.label}</span>
                    <span className={`text-[10px] uppercase tracking-wide text-muted-foreground`}>
                      {t.difficulty}
                    </span>
                    <span className={`ml-1 text-[10px] px-2 py-0.5 rounded-full border ${categoryBadge[t.category]}`}>
                      {t.category}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main area */}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,0.62fr)_minmax(0,1fr)]">
        {/* LEFT: Simple Stepper */}
        <Card className="border-subtle shadow-soft-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <span className={`inline-flex h-8 w-8 items-center justify-center rounded-xl ${a.soft} ${a.text}`}>
                <Layers className="h-4 w-4" />
              </span>
              {activeTrack?.label ?? "Track"} roadmap (steps)
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Clean and motivating stepper — users always know what to learn next.
            </p>
          </CardHeader>

          <CardContent className="space-y-3">
            {stages.length === 0 && (
              <div className="text-sm text-muted-foreground">
                No roadmap steps yet for this track.
              </div>
            )}

            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {stages.map((s, idx) => {
                const isSelected = selectedStage?.id === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => setSelectedStageId(s.id)}
                    className={[
                      "w-full rounded-2xl border px-4 py-3 text-left transition-smooth",
                      isSelected
                        ? `bg-primary/5 border-primary/30 ring-2 ${a.ring}`
                        : "bg-card hover:bg-muted/60 border-subtle",
                    ].join(" ")}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-muted-foreground">
                            Step {idx + 1}
                          </span>
                          <Badge variant="outline" className="text-[10px] uppercase">
                            {s.level}
                          </Badge>
                        </div>

                        <div className="text-sm font-semibold text-foreground">
                          {s.title}
                        </div>

                        <div className="text-xs text-muted-foreground">
                          {s.summary}
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-1 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {s.estimated}
                        </span>
                        {s.videos?.length ? (
                          <span className={`inline-flex items-center gap-1 ${a.text}`}>
                            <PlayCircle className="h-3.5 w-3.5" />
                            {s.videos.length} video{ s.videos.length > 1 ? "s" : "" }
                          </span>
                        ) : (
                          <span className="text-[11px]">No videos yet</span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* RIGHT: Details + Videos */}
        <Card className="border-subtle shadow-soft-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <span className="text-muted-foreground">Study focus</span>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <span className={`${a.text}`}>{selectedStage?.title ?? "Select a step"}</span>
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-5">
            {!selectedStage && (
              <div className="text-sm text-muted-foreground">
                Select a step from the left to view the learning plan.
              </div>
            )}

            {selectedStage && (
              <>
                {/* Topic chips */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Most important topics
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {selectedStage.keyTopics.map((t) => (
                      <span
                        key={t}
                        className={[
                          "rounded-full border px-3 py-1 text-xs",
                          "bg-card hover:bg-muted/70 transition-smooth cursor-default",
                        ].join(" ")}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Videos */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Videos
                  </div>

                  {!selectedStage.videos?.length && (
                    <div className="rounded-2xl border border-subtle p-4 bg-muted/30">
                      <div className="text-sm font-medium">No videos attached yet</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Add videos later from backend, or expand the track content inside <code>src/data/tracks.ts</code>.
                      </div>
                    </div>
                  )}

                  {selectedStage.videos?.map((v) => (
                    <div
                      key={v.id}
                      className="rounded-2xl border border-subtle p-4 bg-card hover:bg-muted/50 transition-smooth"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <PlayCircle className={`h-5 w-5 ${a.text}`} />
                            <a
                              href={v.url}
                              target="_blank"
                              rel="noreferrer"
                              className={`text-sm font-semibold ${a.text} hover:underline`}
                            >
                              {v.title}
                            </a>
                          </div>

                          <div className="text-xs text-muted-foreground">
                            {v.source ?? "Video"}
                            {v.level ? ` • ${v.level}` : ""}
                            {v.duration ? ` • ${v.duration}` : ""}
                          </div>
                        </div>

                        <Button variant="outline" size="sm" asChild className="text-xs">
                          <a href={v.url} target="_blank" rel="noreferrer">
                            Watch
                          </a>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
};
