import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import { RoadmapSourcesPanel } from "@/features/roadmap/components/RoadmapSourcesPanel";
import type { Roadmap } from "@/lib/api";
import { render } from "@/test/utils";

function makeRoadmap(provenance: Record<string, unknown>): Roadmap {
  return {
    id: "roadmap-1",
    title: "Backend Engineer",
    phases: [{ id: "p1", order: 1, title: "Foundations" }],
    metadata: { generation: { provenance } },
  } as unknown as Roadmap;
}

describe("RoadmapSourcesPanel", () => {
  it("renders per-phase source links and the dev-only license note for a sourced roadmap", () => {
    const roadmap = makeRoadmap({
      structure_source: "roadmap.sh",
      fallback_used: false,
      structure_license_tier: "dev_only",
      retrieved_urls: ["https://roadmap.sh/backend"],
      phase_sources: [{ phase_order: 1, urls: ["https://roadmap.sh/backend"] }],
    });

    render(<RoadmapSourcesPanel roadmap={roadmap} />);

    expect(screen.getByText("Foundations")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /roadmap\.sh\/backend/i })).toHaveAttribute(
      "href",
      "https://roadmap.sh/backend",
    );
    expect(screen.getByText(/development-only reference/i)).toBeInTheDocument();
  });

  it("shows the deterministic-template badge for a fallback roadmap instead of fake sources", () => {
    const roadmap = makeRoadmap({
      structure_source: "deterministic_fallback",
      fallback_used: true,
      structure_license_tier: "internal",
      retrieved_urls: [],
      phase_sources: [],
    });

    render(<RoadmapSourcesPanel roadmap={roadmap} />);

    expect(screen.getByText(/Deterministic template/i)).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
