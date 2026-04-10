import { Clock3, Flag, Layers3, Target } from "lucide-react";

import type { Roadmap, RoadmapStats } from "@/lib/api";

interface ProgressSnapshotProps {
  roadmap: Roadmap | null;
  stats: RoadmapStats | null;
}

export function ProgressSnapshot({ roadmap, stats }: ProgressSnapshotProps) {
  const items = [
    {
      label: "Phases complete",
      value: stats ? `${stats.completed_phases}/${stats.total_phases}` : "0/0",
      icon: Layers3,
    },
    {
      label: "Current focus",
      value: roadmap?.journey_summary?.next_action_title ?? "Not set",
      icon: Target,
    },
    {
      label: "Estimated hours",
      value: stats ? `${Math.round(stats.estimated_total_hours)}h` : "0h",
      icon: Clock3,
    },
    {
      label: "Goal level",
      value: roadmap?.target_level || "Not set",
      icon: Flag,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <div className="panel-paper rounded-[1.5rem] p-5" key={item.label}>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="type-kicker">{item.label}</p>
              <p className="mt-3 text-xl font-bold">{item.value}</p>
            </div>
            <div className="rounded-2xl bg-background/80 p-3">
              <item.icon className="h-5 w-5 text-primary" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
