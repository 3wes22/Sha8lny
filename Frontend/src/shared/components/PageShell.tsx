import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageShellProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  aside?: ReactNode;
  className?: string;
  heroClassName?: string;
  contentClassName?: string;
  children: ReactNode;
}

export function PageShell({
  eyebrow,
  title,
  description,
  actions,
  aside,
  className,
  heroClassName,
  contentClassName,
  children,
}: PageShellProps) {
  return (
    <div className={cn("space-y-8", className)}>
      <section className={cn("atlas-panel overflow-hidden p-6 md:p-8 motion-rise", heroClassName)}>
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            {eyebrow ? <p className="type-kicker">{eyebrow}</p> : null}
            <h1 className="text-balance text-4xl font-bold md:text-6xl">{title}</h1>
            {description ? (
              <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
                {description}
              </p>
            ) : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
      </section>

      <div className={cn("grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]", contentClassName)}>
        <div className="space-y-6">{children}</div>
        {aside ? <aside className="space-y-6">{aside}</aside> : null}
      </div>
    </div>
  );
}
