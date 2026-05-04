import { useEffect, useMemo, useState } from "react";
import {
  Brain,
  ChartNetwork,
  FileSearch,
  Lightbulb,
  Microscope,
  Puzzle,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type LoadingPhase = "generating" | "analyzing_stage_1" | "analyzing_stage_2";

interface AssessmentLoadingAnimationProps {
  phase: LoadingPhase;
}

// ---------------------------------------------------------------------------
// Phase Configs
// ---------------------------------------------------------------------------

const phaseConfig: Record<
  LoadingPhase,
  {
    eyebrow: string;
    headline: string;
    description: string;
    facts: string[];
    icon: typeof Brain;
    accentHue: number;
  }
> = {
  generating: {
    eyebrow: "Crafting your assessment",
    headline: "Building targeted questions\njust for you",
    description:
      "Our AI is analyzing your chosen career path and constructing questions that probe real-world readiness — not textbook trivia.",
    facts: [
      "Each question is mapped to a specific sub-skill in your career graph",
      "We calibrate difficulty based on industry expectations",
      "Questions cover theory, application, and professional judgement",
      "Every option is scored on a multi-dimensional rubric",
      "Assessment takes ~5 minutes to complete once ready",
    ],
    icon: Brain,
    accentHue: 20,
  },
  analyzing_stage_1: {
    eyebrow: "Processing stage 1",
    headline: "Analyzing your\nfirst-stage answers",
    description:
      "We're reading your responses to identify knowledge gaps and confidence patterns, so stage 2 can ask the right follow-up questions.",
    facts: [
      "We measure both accuracy and confidence signals",
      "Gap detection identifies areas needing deeper probing",
      "Stage 2 questions will be personalized to your profile",
      "Sub-skill scoring runs across multiple competency dimensions",
      "Your strongest areas are validated with harder scenarios",
    ],
    icon: Microscope,
    accentHue: 188,
  },
  analyzing_stage_2: {
    eyebrow: "Finalizing results",
    headline: "Combining both stages\ninto your assessment",
    description:
      "Both stages are being merged into a comprehensive skill profile that maps directly to your career roadmap.",
    facts: [
      "Cross-referencing stage 1 and stage 2 response patterns",
      "Building your complete sub-skill evidence map",
      "Calculating roadmap priority signals for each gap",
      "Generating prerequisite links between skill areas",
      "Preparing your actionable career development report",
    ],
    icon: ChartNetwork,
    accentHue: 142,
  },
};

const orbitIcons = [Brain, Target, Lightbulb, Puzzle, Zap, FileSearch, Sparkles, Microscope];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AssessmentLoadingAnimation({ phase }: AssessmentLoadingAnimationProps) {
  const config = phaseConfig[phase];
  const PhaseIcon = config.icon;
  const [currentFact, setCurrentFact] = useState(0);
  const [factVisible, setFactVisible] = useState(true);

  // Cycle facts every 4 seconds with a fade transition
  useEffect(() => {
    const interval = setInterval(() => {
      setFactVisible(false);
      setTimeout(() => {
        setCurrentFact((prev) => (prev + 1) % config.facts.length);
        setFactVisible(true);
      }, 400);
    }, 4000);
    return () => clearInterval(interval);
  }, [config.facts.length]);

  // Pick 6 random orbit icons, seeded by phase
  const selectedOrbitIcons = useMemo(() => {
    const shuffled = [...orbitIcons].sort(
      (a, b) => (a.displayName ?? "").localeCompare(b.displayName ?? "") + (phase === "generating" ? 0 : 1),
    );
    return shuffled.slice(0, 6);
  }, [phase]);

  const accentColor = `hsl(${config.accentHue} 80% 55%)`;
  const accentGlow = `hsl(${config.accentHue} 80% 55% / 0.15)`;
  const accentGlowStrong = `hsl(${config.accentHue} 80% 55% / 0.25)`;

  return (
    <div className="relative flex min-h-[85vh] items-center justify-center overflow-hidden">
      {/* ---- Ambient background blobs ---- */}
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
      >
        <div
          className="loading-blob loading-blob--1"
          style={{ background: `radial-gradient(circle, ${accentGlow}, transparent 70%)` }}
        />
        <div
          className="loading-blob loading-blob--2"
          style={{ background: `radial-gradient(circle, ${accentGlowStrong}, transparent 70%)` }}
        />
        <div
          className="loading-blob loading-blob--3"
          style={{ background: `radial-gradient(circle, hsl(${config.accentHue} 60% 50% / 0.1), transparent 70%)` }}
        />
      </div>

      {/* ---- Main content ---- */}
      <div className="relative z-10 mx-auto max-w-3xl px-6 py-12">
        {/* Orbiting animation */}
        <div className="relative mx-auto mb-10 h-52 w-52 md:h-64 md:w-64">
          {/* Orbit rings */}
          <div
            className="loading-ring loading-ring--outer"
            style={{ borderColor: `hsl(${config.accentHue} 70% 55% / 0.15)` }}
          />
          <div
            className="loading-ring loading-ring--inner"
            style={{ borderColor: `hsl(${config.accentHue} 70% 55% / 0.25)` }}
          />

          {/* Orbiting icons */}
          {selectedOrbitIcons.map((Icon, i) => {
            const angle = (360 / selectedOrbitIcons.length) * i;
            const isOuter = i % 2 === 0;
            return (
              <div
                className={`loading-orbit-item ${isOuter ? "loading-orbit-item--outer" : "loading-orbit-item--inner"}`}
                key={Icon.displayName ?? i}
                style={
                  {
                    "--orbit-start-angle": `${angle}deg`,
                    "--orbit-color": accentColor,
                  } as React.CSSProperties
                }
              >
                <Icon className="h-4 w-4 md:h-5 md:w-5" style={{ color: accentColor, opacity: 0.7 }} />
              </div>
            );
          })}

          {/* Center pulsing icon */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div
              className="loading-center-pulse"
              style={{
                background: `linear-gradient(135deg, hsl(${config.accentHue} 80% 50%), hsl(${config.accentHue + 20} 75% 45%))`,
                boxShadow: `0 0 40px ${accentGlowStrong}, 0 0 80px ${accentGlow}`,
              }}
            >
              <PhaseIcon className="h-8 w-8 text-white md:h-10 md:w-10" />
            </div>
          </div>
        </div>

        {/* Text content */}
        <div className="space-y-6 text-center motion-rise">
          <p className="type-kicker" style={{ color: accentColor }}>
            {config.eyebrow}
          </p>

          <h1 className="text-balance text-3xl font-bold leading-tight md:text-5xl whitespace-pre-line">
            {config.headline}
          </h1>

          <p className="mx-auto max-w-lg text-base leading-7 text-muted-foreground md:text-lg">
            {config.description}
          </p>

          {/* Progress bar (infinite shimmer) */}
          <div className="mx-auto max-w-xs">
            <div className="h-1.5 overflow-hidden rounded-full bg-muted/60">
              <div
                className="loading-shimmer-bar h-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, transparent, hsl(${config.accentHue} 80% 55%), transparent)`,
                }}
              />
            </div>
          </div>

          {/* Rotating facts */}
          <div className="mx-auto max-w-md rounded-2xl border border-border/50 bg-card/60 px-6 py-4 backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <Sparkles
                className="mt-0.5 h-4 w-4 shrink-0"
                style={{ color: accentColor }}
              />
              <p
                className="text-sm leading-6 text-muted-foreground transition-opacity duration-300"
                style={{ opacity: factVisible ? 1 : 0 }}
              >
                {config.facts[currentFact]}
              </p>
            </div>

            {/* Fact indicators */}
            <div className="mt-3 flex justify-center gap-1.5">
              {config.facts.map((_, i) => (
                <div
                  className="h-1 rounded-full transition-all duration-300"
                  key={i}
                  style={{
                    width: i === currentFact ? 20 : 6,
                    backgroundColor: i === currentFact ? accentColor : "hsl(var(--muted))",
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
