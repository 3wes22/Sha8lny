# Roadmap Page Redesign — Design Spec

**Date:** 2026-06-20
**Status:** Approved (design direction)
**Scope:** Frontend only. Redesign the `/roadmap` page into a simpler, more dynamic "trail map" experience that matches the existing Career Atlas visual system. No backend or API changes.

> Part of a larger effort to surface every backend feature in the UI. Per agreement, the Roadmap redesign ships first; the new feature pages (Progress, Career Tools, Courses) follow in a later spec.

## 1. Problem

The current `/roadmap` page stacks dense phase panels, each containing a two-column grid of milestone cards, plus a side rail and a sources panel. It reads as "a pile of unrelated progress widgets" and is hard to scan. The goal is a **simpler, more dynamic** page that answers "where am I and what do I do next?" at a glance, drawing on the visual language of route/trail maps (e.g. roadmap.sh) while staying on-brand for the warm, cartographic "Career Atlas" theme.

## 2. Chosen direction

A **vertical journey path ("trail map")**: a single central spine runs top-to-bottom with phases rendered as "stations" along it. Completed phases collapse to one line, the current phase expands with its milestone checklist, and upcoming/locked phases sit faded in a dashed "fog of war" state. Validated as a high-fidelity mockup in the real palette during brainstorming.

"Dynamic" means **both**:
- **Interactive** — smooth expand/collapse of stations, animated progress bar and spine fill, hover lift.
- **Personalized** — the path auto-derives current focus and locked state from the user's live progress and assessment-driven roadmap data.

## 3. Component architecture

`RoadmapPage.tsx` remains the data owner (fetches templates + active roadmap, polls while AI generates). The dense progress view is replaced by a single trail.

| Component | Status | Responsibility |
|-----------|--------|----------------|
| `RoadmapPage.tsx` | Modified | Data fetching/polling (unchanged), simplified layout, header with journey stats |
| `RoadmapTrail.tsx` | New | Vertical spine + ordered list of stations; owns which station is expanded |
| `RoadmapStation.tsx` | New | One phase: map-pin marker + card; renders collapsed / expanded / locked states |
| `RoadmapMilestoneRow.tsx` | New | Checklist row: checkbox toggle, title, type pill, hours |
| `RoadmapSourcesPanel.tsx` | Kept, relocated | Rendered as a collapsed "Why these steps?" disclosure inside the current station |
| `RoadmapAtlas.tsx` | Retired | Replaced by `RoadmapTrail` |
| `RoadmapNodeCard.tsx` | Retired | Replaced by `RoadmapStation` / `RoadmapMilestoneRow` |
| `RoadmapRail.tsx` | Retired | Folded into the trail + header |
| `RoadmapProgressView.tsx` | Retired | Replaced by `RoadmapTrail` |

Template picker moves into a collapsed **"Switch track"** disclosure at the bottom of the page — available but de-emphasized.

No new UI primitive is added; there is no collapsible/accordion primitive in `components/ui`, so expand/collapse uses local React state + CSS transitions.

## 4. Data flow

No backend or API changes. Existing calls only:
- `roadmapTemplateApi.list()`
- `roadmapApi.list({ status })`, `roadmapApi.get(id)`
- `roadmapApi.createFromTemplate(...)`, `roadmapApi.activate(id)`
- `roadmapApi.updateProgress(id, { milestone_id, status })`

Milestone checkbox toggles call `updateProgress` then refetch (existing pattern). Errors surface via `toast` + `getApiErrorMessage` (existing).

## 5. Personalization logic

A pure helper `deriveStationState(phase, index, phases)` returns one of:

- `completed` — phase `status === "completed"` → collapsed, green pin ✓
- `current` — phase `status === "in_progress"` → orange pin ▶, expanded by default, checklist visible
- `next` — the first `not_started` phase after the current one → "up next", available/expandable, not locked
- `locked` — any phase beyond `next` → dashed fog, not expandable, tooltip "Finish {previous} first"

Fallbacks: if no `in_progress` phase exists (fresh roadmap), the first phase becomes `current`. If all phases are completed, the roadmap renders in a "complete" celebratory header state.

The trail spine is a CSS gradient filling green up to the completed portion, orange across the current segment, faded beyond — driven by `roadmap.completion_percentage`. The header pulls `roadmap.journey_summary` for current-focus label and remaining time, and `total_phases` / completion for the stat row.

## 6. Interactivity & motion

- Clicking a non-locked station expands/collapses it (CSS `max-height` + opacity transition). The current station is expanded on first render.
- Progress bar and spine fill animate on mount using the existing `motion-rise` / `transition-smooth` utilities.
- Hover lift via existing `interactive-scale`. Locked stations are inert (no pointer, reduced opacity, dashed border) with an explanatory tooltip.
- All motion respects the existing `prefers-reduced-motion` overrides in `index.css`.

## 7. States & errors

- **Loading** — existing centered spinner.
- **AI generating** — existing poll loop; show a "drawing your route" processing panel.
- **Empty (no roadmap)** — template picker becomes the primary surface with a clear empty-state prompt.
- **Update in flight** — dim the active station (existing opacity pattern).
- **Errors** — `toast.error(getApiErrorMessage(...))`.

## 8. Visual language (on-brand)

- Palette: orange primary (`hsl(20 92% 52%)`), teal accent (`hsl(188 74% 41%)`), success green, cream paper background with faint grid.
- Display font: Space Grotesk; body: IBM Plex Sans.
- Reuse `atlas-panel`, `panel-paper`, `type-kicker`, `gradient-primary`, `shadow-atlas/quiet`, `interactive-scale`, `motion-*`.
- Map-pin station markers; two-tone trail spine; collapsed/expanded/fog station states.

## 9. Testing

- Update `RoadmapPage.test.tsx` and `RoadmapSourcesPanel.test.tsx` for the new structure.
- Add tests for `RoadmapTrail` / `RoadmapStation`: renders all stations, current is expanded, locked station is inert, milestone checkbox triggers `updateProgress`.
- Verify `deriveStationState` with a small unit test (completed/current/next/locked + fallbacks).
- Gates: `npm run test:run`, `npm run build`, `npm run lint`.

## 10. Out of scope

- Backend / API changes.
- Drag-to-reorder phases.
- The new Progress / Career Tools / Courses pages (separate later spec).
- PDF/export of the roadmap.
