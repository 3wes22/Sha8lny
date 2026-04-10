import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export interface JourneyStep {
  id: string;
  label: string;
  description?: string;
  status: "complete" | "current" | "upcoming";
}

interface JourneyProgressProps {
  steps: JourneyStep[];
}

export function JourneyProgress({ steps }: JourneyProgressProps) {
  return (
    <ol className="grid gap-3 md:grid-cols-4">
      {steps.map((step) => (
        <li
          key={step.id}
          className={cn(
            "panel-paper rounded-[1.5rem] p-4 transition-smooth",
            step.status === "current" && "border-primary/30 bg-primary/5",
            step.status === "complete" && "border-success/30 bg-success/10",
          )}
        >
          <div className="flex items-center gap-3">
            <span
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold",
                step.status === "complete" && "border-success bg-success text-success-foreground",
                step.status === "current" && "border-primary bg-primary text-primary-foreground",
                step.status === "upcoming" && "border-border bg-background text-muted-foreground",
              )}
            >
              {step.status === "complete" ? <Check className="h-4 w-4" /> : step.id}
            </span>
            <div>
              <p className="text-sm font-semibold">{step.label}</p>
              {step.description ? (
                <p className="text-xs text-muted-foreground">{step.description}</p>
              ) : null}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
