interface DashboardStat {
  label: string;
  value: string;
}

interface DashboardStatRowProps {
  items: DashboardStat[];
}

export function DashboardStatRow({ items }: DashboardStatRowProps) {
  return (
    <section className="motion-fade grid grid-cols-2 gap-3 sm:grid-cols-4">
      {items.map((item) => (
        <div className="panel-paper rounded-[1.35rem] px-4 py-4" key={item.label}>
          <p className="text-2xl font-bold leading-none text-foreground sm:text-3xl">{item.value}</p>
          <p className="type-kicker mt-2">{item.label}</p>
        </div>
      ))}
    </section>
  );
}
