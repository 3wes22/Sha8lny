# Dashboard Page Redesign — Design Spec

**Date:** 2026-06-20
**Status:** Approved (design direction)
**Scope:** Frontend only. Simplify the `/dashboard` page into a calmer, less cramped single-column layout that keeps the warm "Career Atlas" visual system. No backend or API changes.

> Companion to the 2026-06-20 Roadmap redesign. Same goal: make a dense, widget-piled surface read clearly at a glance.

## 1. Problem

The current `DashboardPage.tsx` is one long editorial composition with oversized typography (`clamp` headlines up to ~7rem, milestone counters up to ~10rem), several nested multi-column grids, and many divider borders. It also repeats information the global app header (`MainLayout`) already shows, and carries self-referential filler copy ("the dashboard should guide the eye…", "narrative surface"). The result reads as cramped and hard to scan. The redesign answers "where am I and what do I do next?" without the visual noise.

## 2. Chosen direction

**Focused single column** (validated as a content-mapped mockup in the real palette during brainstorming). A calm top-to-bottom flow with generous spacing, normal-scale typography, and no headline that competes with the page header above it. Centered, max-width ~680–760px reading column.

Order of blocks:

1. **Welcome band** — kicker + compact greeting (`Welcome back, {firstName}.`) + one-line live status (`You're {N}% through {roadmap title} — {next action}`) + primary CTA (Open roadmap / Start assessment) + secondary (Explore jobs).
2. **Stat row** — 4 compact cards: **Milestones** (`completed/total`), **Phases** (`completed/total`), **Streak** (`{streak} day` / fallback hours / planned), **Horizon** (`{weeks}w`).
3. **Current focus** — active phase title, short description, phase progress `%` + thin progress bar.
4. **Up next** — the next 3 milestones (title · phase · type pill · hours).
5. **Continue exploring** — quiet text links: roadmap, jobs, advisor, profile.

## 3. What gets cut

- Oversized `clamp(...)` headline and 10rem milestone counters.
- Self-referential / meta copy and the "Career Atlas / Narrative surface" framing tags.
- Duplicated roadmap-title block, duplicate "active phase" block, and duplicate "next action insights" block (consolidated into the Welcome band + Current focus).
- The standalone "Completed milestones" history list (the count lives in the stat row). Dropped entirely, per approval.

## 4. Component architecture

`DashboardPage.tsx` stays the data owner (same fetch logic) and renders the simplified column. Extract small presentational pieces so the file stays focused:

| Component | Status | Responsibility |
|-----------|--------|----------------|
| `DashboardPage.tsx` | Rewritten | Data fetching (unchanged), derived values, single-column layout, loading/empty/error states |
| `DashboardWelcome.tsx` | New | Greeting band: kicker, greeting, one-line status, primary/secondary CTAs |
| `DashboardStatRow.tsx` | New | 4 compact stat cards |
| `DashboardFocusCard.tsx` | New | Current phase + description + progress % and bar |
| `DashboardUpNext.tsx` | New | Next-milestones list (empty-state aware) |
| `CareerAtlasHero.tsx` | Retired (delete) | Dead code — never imported |
| `ProgressSnapshot.tsx` | Retired (delete) | Dead code — never imported |

Reuse existing utilities only (`panel-paper`, `atlas-panel`, `type-kicker`, `gradient-primary`, `interactive-scale`, `transition-smooth`, `focus-ring`, `motion-rise/fade`). No new UI primitive.

## 5. Data flow

No backend or API changes. Same calls as today:
- `roadmapApi.list({ status: "in_progress" })`, falling back to `{ status: "active" }`
- `roadmapApi.get(id)`
- `roadmapApi.getStats(id)`

Derived values reused from the current page: `completedMilestoneCount`, `totalMilestoneCount`, `activePhase`, `phaseProgress`, `nextMilestones` (sliced to 3), `nextActionTitle/Summary`, `paceValue`, `streakDays`, `loggedHours`, `estimated_duration_weeks`, `completion_percentage`.

## 6. States

- **Loading** — keep the existing centered spinner block.
- **Error** — keep the existing inline error pill at the top of the column.
- **Empty (no roadmap)** — Welcome band greeting switches to the "map your first direction" copy; status line invites starting an assessment; primary CTA → assessment, secondary → browse templates. Stat row shows zeros; Current focus and Up next render concise empty-state text instead of data. No separate dashed "no roadmap" panel.

## 7. Visual language (on-brand)

- Palette: orange primary (`hsl(20 92% 52%)`), teal accent (`hsl(188 74% 41%)`), success green, cream paper background.
- Display font: Space Grotesk; body: IBM Plex Sans. Greeting ~`text-3xl`, focus title ~`text-xl/2xl`, progress `%` accent in primary. No `clamp` giant type.
- Cards use `panel-paper` / rounded `~1.25–1.5rem`, soft shadows, generous padding; type-pills reuse the teal-tinted accent style; mount animation via `motion-rise`/`motion-fade`; hover lift via `interactive-scale` on interactive elements only. Respects existing `prefers-reduced-motion` overrides.

## 8. Testing

- Update `DashboardPage.test.tsx` for the new structure: assert greeting renders, the 4 stat values appear, current focus phase + progress render, an up-next milestone renders, and streak text renders. Remove assertions tied to deleted copy (e.g. "momentum is already visible", "Completed milestones" history).
- Keep the existing API mock shape (already provides phases, milestones, stats, pace).
- Gates: `npm run test:run`, `npm run build`, `npm run lint`.

## 9. Out of scope

- Backend / API changes.
- New data not already returned by `roadmapApi` (e.g. activity charts).
- Changes to `MainLayout` header.
- The completed-milestones history view (removed, not relocated).
