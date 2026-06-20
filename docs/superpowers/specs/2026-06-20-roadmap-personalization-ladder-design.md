# Roadmap Personalization — Beginner→Job-Ready Ladder with Assessment-Derived Baseline

**Date:** 2026-06-20
**Status:** Draft (pending user review)
**Scope:** Backend roadmap *generation* + thin frontend relabel. Companion to the already-shipped frontend trail-map redesign (`2026-06-20-roadmap-redesign-design.md`), which renders the states this spec produces.

> The trail map already renders `completed` / `skipped` phases as greyed, collapsed "passed" stations (`Frontend/src/features/roadmap/lib/stationState.ts`). The visual the user wants exists. What's missing is the **generation logic that actually marks foundational work as already-passed based on the assessment.** Today every phase and milestone is created `not_started` regardless of the learner's level (`services.py:706`, `:721`), so an advanced learner gets the same from-scratch plan as a total beginner.

## 1. Problem

The roadmap is neither *personalized to prior knowledge* nor *comprehensive*:

1. **No prior-knowledge acknowledgement.** A learner whose assessment shows they're past beginner still gets a roadmap that starts at zero. There is no "you already passed this" greying, even though the UI supports rendering it.
2. **Shallow structure.** The deterministic blueprint is only 3 forward-looking phases ("Stabilize baseline → Close gaps → Ship proof") with generic milestone titles ("Strengthen X foundations"). There is no real beginner→advanced progression, so there is nothing foundational to grey, and it doesn't read as "a very real roadmap."

## 2. Goals / Non-goals

**Goals**
- Generate a real **5-band ladder** (Foundations → Core → Intermediate → Advanced → Job-Ready) with comprehensive, role-specific milestones for **all 8 supported roles**.
- Use the assessment to set the learner's **entry point**: bands/milestones they've already mastered are marked passed (greyed); the rest is the live plan.
- **Hybrid** entry-point logic: overall level sets the baseline band; per-sub-skill signals refine individual milestones. **A band only greys fully when *all* its milestones are passed** — a flagged gap inside an otherwise-passed band stays active as a catch-up item.
- Passed items are **labeled as assessment-derived** and the learner can **revise** (reopen) any of them.
- Demo-reliable: the deterministic ladder is the backbone (no Gemini-quota dependency); Gemini stays a copy-only enhancement layer.

**Non-goals**
- No change to the progress-percentage engine (`apps/progress/services.py`) or its 274-test suite. The design works *with* it.
- No trail-map visual redesign (already shipped).
- No PDF export, no drag-to-reorder, no new UI primitive.

## 3. The 5-band ladder

A fixed, ordered progression shared by all roles; content differs per role.

| # | Band | Theme |
|---|------|-------|
| 1 | **Foundations** | Prerequisites & fundamentals (programming basics, Git/CLI, how the domain works) |
| 2 | **Core Skills** | The role's core stack — the day-one toolkit |
| 3 | **Intermediate** | Applied depth: testing, design, real patterns |
| 4 | **Advanced** | Production concerns: scale, security, observability, tooling |
| 5 | **Job-Ready / Portfolio** | Proof of work + resume/interview + targeted job search |

Each band has: `title`, `description`, `objectives[]`, `weeks`, and `milestones[]`. Each milestone has: `title`, `type` (`course` / `practice` / `project` / `reading`), `hours`, `skills[]`. Bands 2–5 end in a `project`; band 5 contains the portfolio project + job-search milestones (reusing `_portfolio_project_title`).

### Role topic banks (all 8 roles)

Content is authored from public references (roadmap.sh paths, official docs, well-known curricula). Stored as a `ROLE_LADDERS: dict[role_key, list[Band]]` data module. The 8 `SUPPORTED_ROLES` (`apps/assessments/role_graph.py:12`): `backend`, `frontend`, `data_science`, `fullstack`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`.

**Canonical example — `backend`:**

- **Foundations:** Programming fundamentals & a primary language · Git & command line · How the web works (HTTP, DNS, client/server) · Data structures & algorithms basics
- **Core Skills:** A web framework (e.g. Django/Express/Spring) · HTTP & REST API design · Relational databases & SQL · Auth basics (sessions, JWT) → *project: build a CRUD REST API*
- **Intermediate:** ORMs & data modeling · Automated testing (unit/integration) · Error handling & logging · Caching fundamentals · API versioning & pagination → *project: add tests + caching to the API*
- **Advanced:** Scalability & load balancing · Message queues & async workers · Containerization (Docker) · Observability (metrics/tracing) · Security hardening (OWASP) → *project: containerize + add a background worker*
- **Job-Ready:** Ship a production-style backend project · System-design interview prep · Resume & interview stories · Targeted job-search sprint

The other 7 roles follow the same band scaffold with role-appropriate topic lists (authored in implementation), e.g.:
- **frontend:** HTML/CSS/JS fundamentals → a framework + state mgmt + routing → testing/accessibility/perf → SSR/build tooling/PWA → portfolio + interview.
- **data_science:** Python/stats/SQL → pandas/EDA/viz → ML modeling & evaluation → MLOps basics/feature stores/experimentation → end-to-end case study + interview.
- **fullstack:** front + back foundations → core stack both sides → API + DB + auth integration → deployment/CI → full-stack portfolio.
- **devops:** Linux/networking/scripting → CI/CD + IaC → containers/orchestration (K8s) → observability/SRE/security → pipeline portfolio.
- **android:** Kotlin/OOP → Jetpack/Compose/UI → architecture (MVVM)/persistence/networking → performance/CI/publishing → published app + interview.
- **machine_learning_engineer:** Python/math/ML basics → deep learning frameworks → model serving/pipelines → scaling/monitoring/MLOps → deployed model portfolio.
- **ui_ux_designer:** Design fundamentals/color/typography → research/wireframing → design systems/prototyping (Figma) → interaction/accessibility/handoff → case-study portfolio.

A **generic fallback ladder** (role-name-parametrized, mirroring today's `_build_personalized_phase_blueprint` wording) is used for any role not found in `ROLE_LADDERS`, so generation never fails.

### Sizing
Total hours stay driven by `BASE_HOURS_BY_LEVEL` (beginner 96 / intermediate 72 / advanced 54) + `HOURS_PER_FOCUS_ITEM`. Generalize `PHASE_WEEK_SPLIT` (currently 3-way) to a 5-way `LADDER_WEEK_SPLIT = (0.18, 0.22, 0.24, 0.20, 0.16)` (sums to 1.0), with the existing `MIN_PHASE_WEEKS` floor + remainder-borrow guard extended to 5 bands. "Remaining time" in the header is computed from **active (not-passed)** milestones only.

## 4. Assessment-derived baseline (the core new logic)

A pure function `apply_assessment_baseline(phases_data, current_level, gaps, mastered)` runs **after** structure assembly and AI copy-personalization, **before** persistence. It reuses the **already-extracted, already-ranked** lists the service computes today — `gaps` (`_extract_gap_labels`) and `mastered` (`_extract_top_skills` + `strengths`) — so there are no new thresholds to tune. It annotates each milestone dict with `status` and `from_assessment`:

**Coarse step — entry band by level:**

| Level | Entry band index | Pre-passed bands |
|-------|------------------|------------------|
| beginner | 0 | none |
| intermediate | 1 | Foundations |
| advanced | 2 | Foundations + Core |

Milestones in bands *below* the entry index default to **passed**.

**Fine step — refinement from the ranked lists:**
- **Keep-active override:** if a milestone in a *pre-passed* band matches an entry in `gaps`, it stays `not_started` (a catch-up item). → Its band becomes *partial*, not fully grey. **This is the user's rule: don't grey a band if a sub-item isn't passed.**
- **Pre-pass override (symmetric):** if a milestone *at/above* the entry band matches an entry in `mastered`, it may be marked passed even though it sits in the live region.

**Matching** list-entry→milestone is heuristic: case-insensitive token overlap between the (already-humanized) label and the milestone `title` + `skills`. Gaps win ties over mastery (safer to keep work active than to over-grey). Documented as heuristic; no new assessment data required.

## 5. How "passed" is stored — and why it survives the % engine

**Decision: passed milestones get `status = "completed"` + a new boolean `completed_from_assessment = True`** (migration on `RoadmapMilestone`). *Not* `skipped`.

Rationale — the progress recompute (`apps/progress/services.py:97-135`) is the constraint:
- It counts only `COMPLETED` milestones toward % and **auto-derives each phase's status** from its milestones on every update. `skipped` milestones are invisible to it, so a fully-`skipped` band would be reset to `not_started` on the first progress write — wiping the greying.
- With `completed`: a band whose milestones are all completed → engine sets the **phase** `completed` (grey, collapsed). A band with some completed + some active → `in_progress` (partial, **not** fully grey — exactly the catch-up case). A band with none → `not_started`. The learner's "current" band falls out as the first non-finished band (`getCurrentPhaseIndex`, already implemented).
- The headline % then honestly reflects the assessment entry point ("~40% in, based on your assessment").

**Zero changes to the progress engine.** The only new persisted field is `RoadmapMilestone.completed_from_assessment`, which the engine never touches (it only writes status/%/timestamps), so the flag survives recompute.

`_create_personalized_structure` is changed to read `milestone_data.get("status", "not_started")` and `milestone_data.get("from_assessment", False)` instead of hardcoding `not_started`. After persisting, generation calls the existing `ProgressService` recompute once so initial phase statuses and `completion_percentage` are consistent.

## 6. Assessment-derived label + revise (frontend)

- **Serializer:** expose `completed_from_assessment` on `RoadmapMilestoneSerializer` + `RoadmapMilestoneListSerializer`. Add a computed `baseline_from_assessment` on `RoadmapPhaseSerializer` (= phase has ≥1 milestone and every completed/skipped milestone is from-assessment) to drive the band caption — no second stored field, no sync bug.
- **`api.ts`:** add `completed_from_assessment: boolean` to the `RoadmapMilestone` type; optional `baseline_from_assessment?: boolean` on `RoadmapPhase`.
- **`RoadmapMilestoneRow.tsx`:** when `completed_from_assessment`, render `✓ Marked from your assessment` (distinct from a plain completed check) with a **Revise** affordance.
- **`RoadmapStation.tsx`:** when `baseline_from_assessment`, show a band caption like "Set from your assessment — expand to revise". Bands stay expandable, never locked.
- **Revise = reopen** via the *existing* `roadmapApi.updateProgress(id, { milestone_id, status: "not_started" })`. The progress view (`apps/roadmaps/views.py:286`) is extended so that moving a milestone *out of* `completed` clears `completed_from_assessment`. Then the engine recomputes the phase (drops it out of grey if needed).

## 7. AI layer (copy only)

`ai_pipeline.py` `ROADMAP_PERSONALIZATION_PROMPT` changes "fixed 3-phase" → "fixed multi-phase ladder; do not add, remove, or reorder phases or milestones." `_normalize_phases` already iterates the fallback structure generically, so N=5 bands need no structural change. The AI step only rewrites `title`/`description`/`objectives`/`next_action`; it never sees or sets `status`/`from_assessment` (those are applied by `apply_assessment_baseline` after the copy merge), so personalization can't corrupt the baseline.

## 8. Data flow

```
AssessmentResult
  → derive_current_level_from_assessment            (existing: beginner/intermediate/advanced)
  → assemble structure                              (NEW: ROLE_LADDERS[role] 5-band ladder; retrieval/AI as enhancement)
  → RoadmapAIService.personalize_blueprint          (existing: copy only)
  → apply_assessment_baseline(phases, level, gaps, mastered)  (NEW: annotate status + from_assessment)
  → _create_personalized_structure                  (CHANGED: write real statuses + flag, not all not_started)
  → ProgressService recompute                        (existing: derive phase status/% from milestones)
```

The baseline pass runs on the final `phases_data` regardless of whether structure came from the authored ladder, roadmap.sh retrieval, or the generic fallback.

## 9. Testing

**Backend (pytest)**
- `apply_assessment_baseline` unit: beginner → nothing passed; intermediate → Foundations passed, rest active; advanced → Foundations+Core passed; gap-in-passed-band → that milestone stays active + band partial; mastery-above-entry → milestone pre-passed.
- `ROLE_LADDERS` unit: all 8 roles yield 5 non-empty bands; generic fallback for an unknown role.
- Integration: generate for an advanced backend learner → bands 1–2 fully `completed` + `completed_from_assessment`, band 3 current, roadmap `completion_percentage` > 0; reopen a from-assessment milestone → flag cleared, phase recomputed out of `completed`.
- Serializer: `completed_from_assessment` and `baseline_from_assessment` exposed.
- Regression: full backend suite stays green (target: 274+ passing).

**Frontend (vitest)**
- `RoadmapMilestoneRow`: from-assessment row shows "Marked from your assessment", Revise calls `updateProgress(..., not_started)`.
- `RoadmapStation`: band with `baseline_from_assessment` shows the caption; passed bands render grey/collapsed (existing `stationState` behavior).
- Gates: `npm run test:run`, `npm run build`, `npm run lint`.

## 10. Risks & mitigations

- **Sub-skill→milestone matching is heuristic** (token overlap). Acceptable for a formative tool; documented. Coarse level-based entry is the robust backbone if signals are sparse.
- **Authoring 8 role ladders is content volume.** Mitigated by one shared band scaffold + per-role topic banks as plain data, plus a generic fallback so generation never breaks.
- **roadmap.sh licensing** (content is personal-use-only per `assembler.py:26` / root `CLAUDE.md` #5). Per user direction, attribution/publishing is the user's responsibility; not gating this work.

## 11. Out of scope
- Progress-% engine changes; trail-map visual redesign (shipped); PDF export; drag-to-reorder; new UI primitives; changing assessment scoring.
