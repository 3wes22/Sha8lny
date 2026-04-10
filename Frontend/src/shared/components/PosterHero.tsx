import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PosterHeroProps {
  eyebrow: string;
  title: string;
  description: string;
  primaryLabel: string;
  secondaryLabel?: string;
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
  stats?: Array<{ label: string; value: string }>;
  visual?: ReactNode;
  className?: string;
}

export function PosterHero({
  eyebrow,
  title,
  description,
  primaryLabel,
  secondaryLabel,
  onPrimaryClick,
  onSecondaryClick,
  stats = [],
  visual,
  className,
}: PosterHeroProps) {
  return (
    <section className={cn("poster-surface overflow-hidden rounded-[2rem] border border-border/70", className)}>
      <div className="relative grid gap-10 px-6 py-10 md:px-10 md:py-14 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="relative z-10 space-y-6 motion-rise">
          <p className="type-kicker">{eyebrow}</p>
          <h1 className="text-balance max-w-3xl text-5xl font-bold md:text-7xl">{title}</h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-xl">{description}</p>
          <div className="flex flex-wrap gap-3">
            <Button className="btn-scale gradient-primary" onClick={onPrimaryClick} size="lg">
              {primaryLabel}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            {secondaryLabel ? (
              <Button onClick={onSecondaryClick} size="lg" variant="outline">
                {secondaryLabel}
              </Button>
            ) : null}
          </div>
          {stats.length > 0 ? (
            <div className="grid gap-3 pt-4 sm:grid-cols-3">
              {stats.map((stat) => (
                <div className="panel-paper rounded-[1.5rem] p-4" key={stat.label}>
                  <p className="type-kicker">{stat.label}</p>
                  <p className="mt-2 text-2xl font-bold">{stat.value}</p>
                </div>
              ))}
            </div>
          ) : null}
        </div>
        <div className="relative z-10 flex items-end justify-end motion-fade">
          {visual}
        </div>
      </div>
    </section>
  );
}
