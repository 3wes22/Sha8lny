import type { RoadmapPhase } from "@/lib/api";

export type StationState = "completed" | "current" | "next" | "locked";

const isFinished = (status: RoadmapPhase["status"]) =>
  status === "completed" || status === "skipped";

/**
 * Index of the phase the learner is actively on: the in-progress phase if one
 * exists, otherwise the first unfinished phase. Returns -1 when every phase is
 * finished.
 */
export function getCurrentPhaseIndex(phases: RoadmapPhase[]): number {
  const inProgress = phases.findIndex((phase) => phase.status === "in_progress");
  if (inProgress !== -1) {
    return inProgress;
  }
  return phases.findIndex((phase) => !isFinished(phase.status));
}

/**
 * Maps a phase to its trail-map presentation state. Drives the collapsed /
 * expanded / "fog" rendering of stations from live roadmap progress.
 */
export function deriveStationState(
  phase: RoadmapPhase,
  index: number,
  phases: RoadmapPhase[],
): StationState {
  if (isFinished(phase.status)) {
    return "completed";
  }

  const currentIndex = getCurrentPhaseIndex(phases);

  if (currentIndex === -1 || index < currentIndex) {
    return "completed";
  }
  if (index === currentIndex) {
    return "current";
  }
  if (index === currentIndex + 1) {
    return "next";
  }
  return "locked";
}
