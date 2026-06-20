import React, { useEffect, useState } from "react";
import {
  Award,
  BookOpenCheck,
  CalendarClock,
  Clock,
  Flame,
  Loader2,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";

import { PageShell } from "@/shared/components/PageShell";
import { SectionHeader } from "@/shared/components/SectionHeader";
import { StatePanel } from "@/shared/components/StatePanel";
import {
  getApiErrorMessage,
  progressApi,
  type CourseCompletionListItem,
  type MilestoneAchievementListItem,
  type ProgressStats,
} from "@/lib/api";

const formatNumber = (value: string | number | null | undefined, fractionDigits = 1) => {
  const parsed = Number(value ?? 0);
  return Number.isInteger(parsed) ? String(parsed) : parsed.toFixed(fractionDigits);
};

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
};

interface StatTileProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
}

const StatTile: React.FC<StatTileProps> = ({ icon, label, value, hint }) => (
  <div className="panel-paper card-elevated flex flex-col gap-2 rounded-2xl p-5">
    <div className="flex items-center justify-between">
      <span className="type-kicker text-[0.65rem]">{label}</span>
      <span className="rounded-xl bg-background/80 p-2 text-primary">{icon}</span>
    </div>
    <p className="text-3xl font-bold">{value}</p>
    {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
  </div>
);

const ProgressPage: React.FC = () => {
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [achievements, setAchievements] = useState<MilestoneAchievementListItem[]>([]);
  const [completions, setCompletions] = useState<CourseCompletionListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        const [statsData, achievementsData, completionsData] = await Promise.all([
          progressApi.getStats(),
          progressApi.recentAchievements(),
          progressApi.completions(),
        ]);
        if (!active) return;
        setStats(statsData);
        setAchievements(achievementsData ?? []);
        setCompletions(completionsData.results ?? []);
      } catch (error) {
        if (active) toast.error(getApiErrorMessage(error, "Failed to load progress"));
      } finally {
        if (active) setLoading(false);
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <PageShell
      description="Your learning momentum at a glance — hours invested, streaks kept, courses finished, and milestones earned."
      eyebrow="Progress"
      title="Learning progress"
    >
      {loading ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatTile
              hint={`This week: ${formatNumber(stats?.this_week_hours)} h`}
              icon={<Clock className="h-4 w-4" />}
              label="Total hours"
              value={formatNumber(stats?.total_learning_hours)}
            />
            <StatTile
              hint={`Longest: ${stats?.longest_streak_days ?? 0} days`}
              icon={<Flame className="h-4 w-4" />}
              label="Day streak"
              value={String(stats?.current_streak_days ?? 0)}
            />
            <StatTile
              icon={<BookOpenCheck className="h-4 w-4" />}
              label="Courses completed"
              value={String(stats?.total_courses_completed ?? 0)}
            />
            <StatTile
              icon={<Trophy className="h-4 w-4" />}
              label="Milestones earned"
              value={String(stats?.total_milestones_achieved ?? 0)}
            />
            <StatTile
              hint={`${stats?.roadmaps_completed ?? 0} completed`}
              icon={<CalendarClock className="h-4 w-4" />}
              label="Active roadmaps"
              value={String(stats?.roadmaps_in_progress ?? 0)}
            />
            <StatTile
              hint={`Last active ${formatDate(stats?.last_activity_date)}`}
              icon={<Clock className="h-4 w-4" />}
              label="Avg hours / day"
              value={formatNumber(stats?.average_daily_hours)}
            />
          </div>

          <section className="space-y-4">
            <SectionHeader
              description="Milestones you've earned in the last 30 days."
              eyebrow="Achievements"
              title="Recent achievements"
            />
            {achievements.length === 0 ? (
              <StatePanel
                description="Complete milestones in your roadmap to start earning badges."
                state="empty"
                title="No achievements yet"
              />
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {achievements.map((achievement) => (
                  <div
                    className="panel-paper card-elevated flex items-start gap-3 rounded-2xl p-4"
                    key={achievement.id}
                  >
                    <span className="rounded-xl bg-primary/10 p-2 text-primary">
                      <Award className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="font-semibold leading-tight">{achievement.milestone_title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(achievement.achieved_at)}
                        {achievement.badge_type ? ` · ${achievement.badge_type} badge` : ""}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <SectionHeader
              description="Courses you've marked as completed."
              eyebrow="History"
              title="Completed courses"
            />
            {completions.length === 0 ? (
              <StatePanel
                description="Finished courses will appear here once you record completions."
                state="empty"
                title="No completed courses yet"
              />
            ) : (
              <div className="atlas-panel divide-y divide-border/60 overflow-hidden">
                {completions.map((completion) => (
                  <div
                    className="flex items-center justify-between gap-4 px-5 py-4"
                    key={completion.id}
                  >
                    <div>
                      <p className="font-medium">{completion.course_title}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        Completed {formatDate(completion.completed_at)}
                        {completion.rating_display ? ` · rated ${completion.rating_display}` : ""}
                      </p>
                    </div>
                    {completion.has_certificate ? (
                      <span className="type-kicker text-[0.6rem] text-success">Certified</span>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </PageShell>
  );
};

export default ProgressPage;
