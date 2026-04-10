# Frontend / Backend Interface Contract

## Scope

This contract captures the backend touchpoints that the frontend reconstruction depends on. It does not require a full API rewrite; it defines the minimum state and payload clarity needed for the redesigned experience.

## 1. Route-Level Frontend Surface Contract

| Frontend Surface | Frontend Route | Backend Dependency | Required Contract Behavior |
|------------------|----------------|--------------------|----------------------------|
| Landing / marketing | `/` | None or public content | Must not depend on authenticated API state for first render |
| Login / register / forgot password | `/login`, `/register`, `/forgot-password` | `users/auth/*` | Must provide clear success/failure messaging and session transitions |
| Dashboard | `/dashboard` | `users`, `roadmap`, `notifications`, possibly `assessment` summaries | Must return enough summary state to identify next actions and current progress |
| Roadmap | `/roadmap` | `roadmap/*` | Must expose roadmap hierarchy and progress state cleanly enough for atlas-style presentation |
| Assessment flow | `/assessment`, `/assessment/session/:assessmentId`, `/assessment/results/:assessmentId` | `assessment/*` | Must distinguish draft, submit, processing, success, and failure states explicitly |
| Jobs | `/jobs`, `/jobs/saved`, `/jobs/:jobId` | `jobs/*` | Must support search/list/detail/save state without broken navigation or fake apply actions |
| Notifications | `/notifications` | `notifications/*` | Must return counts and list state usable in shell badge and dedicated page |
| Profile / settings | `/profile`, `/settings` | `users/*` | Must return user profile and preferences in stable typed shapes |
| Advisory | `/advisor` | `advisory/*` | Must preserve chat history, response, and error state signaling |

## 2. Required API State Expectations

### Assessment

- `GET /assessment/:id/result/` MUST continue to distinguish in-progress work from completed results.
- The frontend can consume `202 Accepted` for processing, but the redesign benefits from stable status metadata if the backend exposes it.
- Any assessment-question payload used for quiz-style rendering MUST include the information required to show progress, question type, and answer choices clearly.

### Roadmap

- Roadmap payloads SHOULD expose clear phase, milestone, and completion relationships.
- If the current payload is too flat for atlas-style presentation, the backend MAY add a presentation-friendly hierarchy or derived summary fields.
- Progress mutations MUST keep status transitions explicit so the UI can style locked, available, active, and completed states without guesswork.

### Jobs

- Search/list/detail payloads MUST maintain stable identifiers, display metadata, and save-state compatibility.
- Saved-job endpoints MUST allow the frontend to render consistent save/remove state across list, saved, and detail surfaces.
- Detail payloads MUST make it obvious whether an external apply URL exists.

### Notifications

- Stats and list payloads MUST remain available for both the nav-shell badge and the dedicated notifications page.
- Mark-read and mark-all-read behavior SHOULD return enough state for optimistic or immediate UI feedback.

## 3. Typed Frontend Consumers

The following frontend consumers are expected to remain authoritative unless this plan explicitly changes them:

- `Frontend/src/lib/api.ts`
- `Frontend/src/features/assessment/routes/*`
- `Frontend/src/features/jobs/routes/*`
- `Frontend/src/features/notifications/routes/*`
- `Frontend/src/shared/layout/MainLayout.tsx`

## 4. Allowed Backend Change Scope

Allowed contract changes for this feature:

- Add derived summary fields for roadmap hierarchy or dashboard next-step emphasis.
- Normalize assessment status or progression metadata for quiz-style rendering.
- Clarify notification counts/list shape where needed for shared shell and dedicated page consistency.
- Clarify job save/detail fields where current payloads force frontend workarounds.

Not part of this feature by default:

- Replacing the authentication system.
- Replatforming the entire API.
- Introducing new AI providers or background-processing infrastructure solely for the redesign.
