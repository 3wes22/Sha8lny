# Research: Sha8alny Frontend Visual Reconstruction

## Sources Reviewed

- roadmap.sh homepage: https://roadmap.sh/
- Genially quiz templates index: https://genially.com/templates/quizzes/
- Work Style Quiz transcript: https://view.genially.com/697adab4f81b4bde1de9d21e/interactive-content-work-style-quiz
- Onboarding Quiz for New Employees transcript: https://view.genially.com/6970f1dbd17aba27389f9a24/interactive-content-onboarding-quiz-for-new-employees
- Corporate Role Quiz transcript: https://view.genially.com/6936e2af4b780bb30cd54ba3/interactive-content-corporate-role-quiz
- Professional Quiz Test transcript: https://view.genially.com/692d7bea0e7c330340ed85ff/interactive-content-professional-quiz-test

## Decision 1: Reconstruct on the current Vite + React base

**Decision**: Keep the current Vite + React + TypeScript frontend as the implementation base instead of combining the redesign with a framework migration.

**Rationale**: The repository already contains a working, cleaned frontend with feature ownership under `Frontend/src/features/*`, a centralized route shell under `Frontend/src/app/*`, and a shared API layer in `Frontend/src/lib/api.ts`. Rebuilding the visual system on this base improves delivery speed and keeps the current repo cleanup useful instead of discarding it.

**Alternatives considered**:

- Migrate to Next.js during the redesign: rejected because it would mix visual reconstruction with a platform migration and slow delivery.
- Import an external template wholesale: rejected because it would not align with current route logic, API integration, or product modules.

## Decision 2: Use a roadmap.sh-inspired "career atlas" direction for the core app shell

**Decision**: Use roadmap.sh as the main inspiration for roadmap and dashboard information architecture: dense but readable hierarchy, journey-first presentation, and category-driven learning navigation.

**Rationale**: The roadmap.sh homepage emphasizes role-based roadmaps, skill-based roadmaps, and learning-path exploration rather than generic dashboard cards. That is directly aligned with Sha8alny’s roadmap, assessment follow-up, and career growth positioning.

**Alternatives considered**:

- Standard SaaS dashboard cards: rejected because they flatten the learning journey into metrics without narrative or pathfinding.
- Highly animated game UI: rejected because it would reduce trust for career planning and assessment results.

## Decision 3: Select "Work Style Quiz" as the primary Genially reference

**Decision**: Use **Work Style Quiz** as the primary Genially template direction for assessment and onboarding-adjacent experiences.

**Rationale**: The Work Style Quiz transcript frames the interaction around professional identity, work environment, strengths, risks, and profile-style outcomes. That tone matches Sha8alny’s career guidance positioning better than generic scoring or internal-corporate training patterns. It also supports a visual-choice format without feeling childish.

**Alternatives considered**:

- **Professional Quiz Test**: strong structural fallback for scored flows, but too generic and exam-like as the main inspiration.
- **Corporate Role Quiz**: rejected because it feels like internal corporate training rather than career discovery.
- **Onboarding Quiz for New Employees**: useful for warmth and icebreaking, but too lightweight and HR-oriented for the main assessment direction.

## Decision 4: Keep route ownership feature-based and introduce a shared visual system instead of page-by-page styling

**Decision**: Apply the redesign through shared visual primitives, layout rules, and feature-owned presentation modules instead of isolated page rewrites.

**Rationale**: The frontend has already been reorganized into `app`, `features`, `shared`, and `components/ui`. A system-level reconstruction will keep dashboard, roadmap, jobs, notifications, and assessment visually coherent while avoiding repeated ad hoc styling.

**Alternatives considered**:

- Restyle each route independently: rejected because it would recreate inconsistency and duplicate logic.
- Build a separate design-system package: rejected as unnecessary overhead for the current repo scale.

## Decision 5: Allow selective backend contract cleanup to support richer UI state

**Decision**: Keep existing module ownership but allow targeted backend contract changes where the frontend needs clearer state or hierarchy data.

**Rationale**: The redesign touches roadmap hierarchy, async assessment states, notifications, and jobs. Some current routes already work, but the reconstruction should not be forced to fake graph state, quiz progress metadata, or processing cues on the client when the backend can return clearer contract data.

**Alternatives considered**:

- Freeze all backend contracts: rejected because it would force UI workarounds and fake state.
- Broad backend rewrite first: rejected because the frontend reconstruction can proceed with targeted endpoint and payload improvements instead.

## Decision 6: Use dual-format roadmap presentation for responsive behavior

**Decision**: Present roadmap-heavy content as a graph or atlas-style journey on larger screens and collapse it into a guided linear journey on smaller screens.

**Rationale**: A roadmap.sh-inspired layout works well on larger screens but can become unreadable on mobile if preserved literally. A dual-format approach keeps the same information architecture while protecting usability.

**Alternatives considered**:

- Same dense graph on every breakpoint: rejected because mobile readability would suffer.
- Separate mobile-only content model: rejected because it would fragment logic and increase maintenance.

## Decision 7: Use an editorial "career atlas" art direction instead of neutral SaaS styling

**Decision**: Push the product toward an editorial career-atlas visual language with stronger typography, restrained color, and spatial hierarchy rather than a generic startup dashboard look.

**Rationale**: The project scope spans learning paths, assessments, jobs, and advisory. A neutral SaaS pattern would make those flows feel interchangeable with ordinary productivity tools, while a stronger atlas direction gives the product a memorable identity without becoming theatrical.

**Alternatives considered**:

- Minimal neutral SaaS restyle: rejected because it would still feel too common and low-identity.
- Highly decorative futuristic UI: rejected because it would create novelty without clarity.

## Decision 8: Split the art direction between public poster-like surfaces and calm product surfaces

**Decision**: Make the landing and public auth flow bolder and image-led, while keeping the authenticated application dense, restrained, and utility-driven.

**Rationale**: The marketing surface needs stronger brand presence, but the logged-in product needs orientation and decision support. One visual language should connect them, but they should not use the same compositional intensity.

**Alternatives considered**:

- Apply the same hero-heavy style everywhere: rejected because product usability would suffer.
- Keep every screen equally quiet: rejected because the product would lose first-impression impact.

## Decision 9: Avoid cards by default and build layout-led information hierarchy

**Decision**: Default to rails, columns, dividers, journey nodes, and section blocks instead of wrapping every feature in cards.

**Rationale**: The current frontend can easily regress into a card mosaic. The redesign should use cards only when the card is the interaction itself, such as a selectable choice or a journey node that acts as a destination.

**Alternatives considered**:

- Traditional dashboard-card grids: rejected because they flatten hierarchy and make the product feel generic.
- Border-heavy panelization: rejected because it adds chrome without improving scanning.

## Decision 10: Bake motion into the plan as a hierarchy tool, not decoration

**Decision**: Require a small set of intentional motions across the redesign: one entrance sequence, one scroll/sticky reveal pattern, and one hover/layout transition family.

**Rationale**: Without explicit motion goals, the implementation is likely to fall back to static layout plus small button hovers. A restrained motion system will make the product feel more current while preserving credibility.

**Alternatives considered**:

- No motion beyond default transitions: rejected because it would undersell the redesign.
- Heavy animation across all surfaces: rejected because it would distract from task completion.
