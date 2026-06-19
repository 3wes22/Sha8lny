import { ExternalLink } from "lucide-react";

import type { Roadmap } from "@/lib/api";

interface RoadmapSourcesPanelProps {
  roadmap: Roadmap;
}

type PhaseSource = {
  phase_order?: number;
  urls?: string[];
  doc_ids?: string[];
};

type RoadmapProvenance = {
  structure_source?: string;
  retrieved_urls?: string[];
  fallback_used?: boolean;
  structure_license_tier?: string;
  phase_sources?: PhaseSource[];
};

function getProvenance(roadmap: Roadmap): RoadmapProvenance | null {
  const generation = roadmap.metadata?.generation;
  if (!generation || typeof generation !== "object") {
    return null;
  }
  const provenance = (generation as { provenance?: RoadmapProvenance }).provenance;
  return provenance && typeof provenance === "object" ? provenance : null;
}

export function RoadmapSourcesPanel({ roadmap }: RoadmapSourcesPanelProps) {
  const provenance = getProvenance(roadmap);
  if (!provenance) {
    return null;
  }

  if (provenance.fallback_used) {
    return (
      <div className="panel-paper rounded-[1.25rem] p-4">
        <span className="inline-flex items-center rounded-full border border-border/60 bg-muted/40 px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
          Deterministic template
        </span>
        <p className="mt-2 text-sm text-muted-foreground">
          This roadmap was generated from an internally authored template (no external sources
          retrieved). Connect the career knowledge base and re-run generation to attach roadmap.sh
          references.
        </p>
      </div>
    );
  }

  const phaseSources = provenance.phase_sources?.length
    ? provenance.phase_sources
    : roadmap.phases?.map((phase, index) => ({
        phase_order: index + 1,
        urls: provenance.retrieved_urls ?? [],
      })) ?? [];

  const visiblePhases = phaseSources.filter((phase) => (phase.urls?.length ?? 0) > 0);
  if (visiblePhases.length === 0) {
    return null;
  }

  return (
    <div className="panel-paper rounded-[1.5rem] p-5">
      <p className="type-kicker">Sources</p>
      <p className="mt-2 text-sm text-muted-foreground">
        Structure retrieved from {provenance.structure_source ?? "roadmap.sh"} at generation time.
      </p>
      {provenance.structure_license_tier === "dev_only" ? (
        <p className="mt-1 text-xs text-muted-foreground/80">
          roadmap.sh is used as a development-only reference (personal-use license) — not
          redistributed as part of the defended corpus.
        </p>
      ) : null}
      <div className="mt-4 space-y-4">
        {visiblePhases.map((phase) => {
          const phaseTitle =
            roadmap.phases?.find((item) => item.order === phase.phase_order)?.title ??
            `Phase ${phase.phase_order ?? "?"}`;

          return (
            <div className="rounded-[1rem] border border-border/60 p-3" key={`${phase.phase_order}-${phaseTitle}`}>
              <p className="text-sm font-semibold">{phaseTitle}</p>
              <ul className="mt-2 space-y-2">
                {(phase.urls ?? []).map((url) => (
                  <li key={url}>
                    <a
                      className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      href={url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {url.replace(/^https?:\/\//, "")}
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
