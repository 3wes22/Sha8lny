import { describe, expect, it } from "vitest";

import type { RoadmapPhase } from "@/lib/api";
import { deriveStationState } from "@/features/roadmap/lib/stationState";

const phase = (status: RoadmapPhase["status"]): RoadmapPhase =>
  ({
    id: `p-${status}-${Math.random()}`,
    title: "Phase",
    description: "",
    order: 1,
    estimated_duration_weeks: 2,
    status,
    completion_percentage: "0",
    objectives: [],
  }) as RoadmapPhase;

describe("deriveStationState", () => {
  it("marks a completed phase as completed", () => {
    const phases = [phase("completed"), phase("in_progress"), phase("not_started")];
    expect(deriveStationState(phases[0], 0, phases)).toBe("completed");
  });

  it("marks the in_progress phase as current", () => {
    const phases = [phase("completed"), phase("in_progress"), phase("not_started")];
    expect(deriveStationState(phases[1], 1, phases)).toBe("current");
  });

  it("marks the phase right after the current one as next", () => {
    const phases = [phase("completed"), phase("in_progress"), phase("not_started"), phase("not_started")];
    expect(deriveStationState(phases[2], 2, phases)).toBe("next");
  });

  it("marks phases beyond next as locked", () => {
    const phases = [phase("completed"), phase("in_progress"), phase("not_started"), phase("not_started")];
    expect(deriveStationState(phases[3], 3, phases)).toBe("locked");
  });

  it("treats the first phase of a fresh roadmap as current, then next, then locked", () => {
    const phases = [phase("not_started"), phase("not_started"), phase("not_started")];
    expect(deriveStationState(phases[0], 0, phases)).toBe("current");
    expect(deriveStationState(phases[1], 1, phases)).toBe("next");
    expect(deriveStationState(phases[2], 2, phases)).toBe("locked");
  });

  it("marks every phase completed when the whole roadmap is done", () => {
    const phases = [phase("completed"), phase("completed")];
    expect(deriveStationState(phases[0], 0, phases)).toBe("completed");
    expect(deriveStationState(phases[1], 1, phases)).toBe("completed");
  });

  it("treats a skipped phase as completed (collapsed)", () => {
    const phases = [phase("skipped"), phase("in_progress")];
    expect(deriveStationState(phases[0], 0, phases)).toBe("completed");
  });
});
