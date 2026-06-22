interface DashboardFocusCardProps {
  title: string;
  description: string;
  progress: number;
}

export function DashboardFocusCard({ title, description, progress }: DashboardFocusCardProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(progress)));

  return (
    <section className="panel-paper rounded-[1.6rem] px-6 py-6 sm:px-7">
      <div className="flex items-start justify-between gap-6">
        <div className="min-w-0 space-y-2">
          <p className="type-kicker">Current focus</p>
          <h2 className="text-balance text-xl font-bold leading-tight text-foreground sm:text-2xl">
            {title}
          </h2>
          <p className="max-w-xl text-sm leading-6 text-foreground/70">{description}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-4xl font-bold leading-none text-primary">{clamped}%</p>
          <p className="type-kicker mt-2">phase</p>
        </div>
      </div>

      <div className="mt-5 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-smooth"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </section>
  );
}
