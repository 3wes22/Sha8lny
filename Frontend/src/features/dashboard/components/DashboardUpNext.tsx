import type { RoadmapMilestone } from "@/lib/api";

type UpNextMilestone = RoadmapMilestone & { phaseName?: string };

interface DashboardUpNextProps {
  milestones: UpNextMilestone[];
  fallbackText: string;
}

export function DashboardUpNext({ milestones, fallbackText }: DashboardUpNextProps) {
  return (
    <section className="panel-paper rounded-[1.6rem] px-6 py-6 sm:px-7">
      <p className="type-kicker">Up next</p>

      {milestones.length > 0 ? (
        <ul className="mt-4 divide-y divide-border/50">
          {milestones.map((milestone) => (
            <li className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0" key={milestone.id}>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">{milestone.title}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="truncate">{milestone.phaseName ?? "Current route"}</span>
                  {milestone.milestone_type ? (
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-[0.1em] text-accent">
                      {milestone.milestone_type}
                    </span>
                  ) : null}
                </div>
              </div>
              <span className="shrink-0 text-xs font-medium text-muted-foreground">
                {milestone.estimated_duration_hours}h
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm leading-6 text-muted-foreground">{fallbackText}</p>
      )}
    </section>
  );
}
