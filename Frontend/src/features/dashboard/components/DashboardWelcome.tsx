import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";

interface DashboardWelcomeProps {
  greeting: string;
  statusText: string;
  primaryLabel: string;
  primaryTo: string;
}

export function DashboardWelcome({ greeting, statusText, primaryLabel, primaryTo }: DashboardWelcomeProps) {
  return (
    <section className="panel-paper motion-rise rounded-[1.75rem] px-6 py-7 sm:px-8 sm:py-8">
      <p className="type-kicker">Dashboard</p>
      <h1 className="mt-3 text-balance text-3xl font-bold leading-tight text-foreground sm:text-4xl">
        {greeting}
      </h1>
      <p className="mt-3 max-w-2xl text-base leading-7 text-foreground/72">{statusText}</p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-smooth [--interactive-hover-scale:1.014] [--interactive-lift:2px] hover:bg-primary/90"
          to={primaryTo}
        >
          {primaryLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
        <Link
          className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 px-5 py-3 text-sm font-medium transition-smooth [--interactive-lift:1px] hover:bg-background/82"
          to={ROUTES.jobs}
        >
          Explore jobs
        </Link>
      </div>
    </section>
  );
}
