import type { ReactNode } from "react";
import { CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";

interface ChoiceCardProps {
  title: string;
  description?: string;
  meta?: string;
  selected?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  icon?: ReactNode;
}

export function ChoiceCard({
  title,
  description,
  meta,
  selected = false,
  disabled = false,
  onClick,
  icon,
}: ChoiceCardProps) {
  return (
    <button
      className={cn(
        "panel-paper card-elevated flex w-full flex-col gap-3 rounded-[1.5rem] p-5 text-left",
        selected && "border-primary/35 bg-primary/5",
        disabled && "cursor-not-allowed opacity-50",
      )}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {icon ? <div className="rounded-2xl bg-background/80 p-3">{icon}</div> : null}
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
          </div>
        </div>
        {selected ? <CheckCircle2 className="h-5 w-5 text-primary" /> : null}
      </div>
      {meta ? <p className="type-kicker text-[0.68rem]">{meta}</p> : null}
    </button>
  );
}
