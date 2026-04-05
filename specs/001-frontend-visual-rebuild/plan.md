# Implementation Plan: Sha8alny Frontend Visual Reconstruction

**Branch**: `[001-frontend-visual-rebuild]` | **Date**: 2026-04-04 | **Spec**: [/Users/mohamed3wes/Downloads/Grad-Project/specs/001-frontend-visual-rebuild/spec.md](/Users/mohamed3wes/Downloads/Grad-Project/specs/001-frontend-visual-rebuild/spec.md)  
**Input**: Feature specification from `/specs/001-frontend-visual-rebuild/spec.md`

## Summary

Reconstruct the Sha8alny frontend around a clearer career-atlas visual system: roadmap.sh-inspired learning-path presentation for roadmap and dashboard surfaces, paired with a professional visual-quiz interaction model for assessment and onboarding-style flows. The implementation will stay on the current Vite + React + TypeScript base, preserve the feature-first frontend structure created during cleanup, and allow selective backend contract changes where the existing API does not provide enough presentation state for roadmap hierarchy, assessment progression, or status-rich user flows. The visual bar is explicitly higher than a standard SaaS refresh: the landing flow should feel poster-like and branded, while the authenticated product should feel editorial, dense, and calm rather than card-heavy.

## Frontend Direction

**Visual Thesis**: Sha8alny should feel like a modern career atlas for ambitious Egyptian learners: editorial, spatial, and precise, with warm paper-like depth, dark graphite structure, and one sharp wayfinding accent.

**Content Plan**:

- **Hero**: Brand-first, full-bleed landing composition with one dominant image or visual plane, short promise, and clear action.
- **Support**: One concrete proof area that explains roadmap, assessment, and job relevance without drifting into card mosaics.
- **Detail**: Product-depth sections that show the roadmap journey, assessment interaction model, and real operating surfaces.
- **Final CTA**: Clean conversion section that returns the user to start, sign in, or continue their path.

**Interaction Thesis**:

- Use one memorable entrance sequence on public surfaces so the product feels intentional on first load.
- Use one scroll-linked or sticky reveal pattern for roadmap or narrative sections where hierarchy matters.
- Use one sharp hover or layout transition pattern that improves scanning across journey nodes, choice cards, or navigation states.

**Surface Rules**:

- Marketing and public auth surfaces should use bold composition, strong brand presence, and full-bleed or near full-bleed visual anchors.
- Authenticated product surfaces should use utility-first copy, minimal chrome, stronger typography, and layout-led hierarchy instead of stacked dashboard cards.
- The roadmap should be the signature visual object of the product, not just another content panel.
- The assessment flow should feel interactive and premium, but never playful enough to undermine trust in the results.
- The design system should use at most two type families and one primary accent color across the product unless a stronger reason emerges during implementation.

## Technical Context

**Language/Version**: TypeScript 5.8 on React 18.3 frontend; Python 3.13 backend support for contract changes  
**Primary Dependencies**: React Router 6, TanStack Query 5, Tailwind CSS 3, Radix UI primitives, Django REST Framework  
**Storage**: Existing Django-managed relational persistence and API-driven frontend state; no new product data store planned  
**Testing**: Vitest + Testing Library, `vite build`, Django `manage.py check`, pytest in affected backend apps  
**Target Platform**: Responsive web application for desktop and mobile browsers  
**Project Type**: Web application with modular-monolith backend and SPA frontend  
**Performance Goals**: Preserve smooth primary navigation, keep roadmap interactions visually legible under typical user data volumes, keep key entrance and hover motions smooth on mobile, and avoid noticeable regression in first-load or authenticated-route responsiveness  
**Constraints**: Preserve existing module boundaries, keep current Vite frontend as implementation base, support async assessment states, avoid exposing broken or placeholder routes during reconstruction, and avoid defaulting back to generic card-grid layouts  
**Scale/Scope**: Redesign public auth/landing plus the main authenticated surfaces across dashboard, roadmap, assessment, jobs, advisory, notifications, profile, and settings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Module boundaries**: PASS. Primary ownership stays in `Frontend/src/app`, `Frontend/src/features/*`, and `Frontend/src/shared/*`. Backend impact is limited to the existing Django apps that already serve the affected flows, mainly `assessments`, `roadmaps`, `jobs`, `notifications`, and `users`.
- **Contract impact**: PASS. This feature explicitly documents route expectations, API touchpoints, async assessment state handling, and typed frontend-consumer changes in `contracts/frontend-backend-interface.md`.
- **Verification**: PASS with required follow-through. Frontend regression coverage is required for critical route behavior and assessment state transitions; backend verification is required only where payloads or route behavior change.
- **AI/data handling**: PASS. The redesign does not introduce new AI providers, but it must preserve clear communication for advisory and assessment flows that depend on backend AI services and personal career data.
- **Operational visibility**: PASS. Any backend changes for async assessment, notifications, or roadmap state must preserve explicit status/error signaling so the redesigned frontend does not hide failure modes behind visuals.

## Project Structure

### Documentation (this feature)

```text
specs/001-frontend-visual-rebuild/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── frontend-backend-interface.md
│   └── ui-experience-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
Backend/
├── apps/
│   ├── assessments/
│   ├── jobs/
│   ├── notifications/
│   ├── roadmaps/
│   └── users/
└── config/

Frontend/
├── src/
│   ├── app/
│   ├── components/ui/
│   ├── features/
│   │   ├── advisory/
│   │   ├── assessment/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── jobs/
│   │   ├── marketing/
│   │   ├── notifications/
│   │   ├── profile/
│   │   ├── roadmap/
│   │   └── settings/
│   ├── hooks/
│   ├── lib/
│   ├── shared/
│   └── test/
└── package.json

ai-models/
└── src/
    └── rag/
```

**Structure Decision**: Use the existing web-application split across `Backend/` and `Frontend/`, keeping the cleaned feature-first frontend layout as the implementation base. No framework migration is part of this feature; the reconstruction happens as a vertical redesign and logic-hardening effort inside the current architecture.

## Post-Design Constitution Check

- **Module boundaries**: PASS. No new top-level project or cross-cutting abstraction is required.
- **Contract-first interfaces**: PASS. Design artifacts explicitly capture UI surface rules and backend contract expectations before tasks.
- **Testable business logic**: PASS. Critical path verification is called out in `quickstart.md` and the interface contract.
- **Responsible AI & data protection**: PASS. Assessment/advisory states remain explicit and no new secret handling is introduced.
- **Operational visibility & simplicity**: PASS. The plan prefers selective contract cleanup over infrastructure expansion.

## Complexity Tracking

No constitutional violations are currently justified for this feature.
