# Frontend Integration Guide

## Purpose

This document describes the current Sha8alny frontend after the visual reconstruction work on `001-frontend-visual-rebuild`. It is the backend-facing reference for:

- how the client is structured,
- which frontend contracts are now expected by each module,
- where route ownership lives,
- and what was validated in the current implementation pass.

## Current Stack

- React 18
- Vite 5
- TypeScript
- React Router
- TanStack Query
- Tailwind + shadcn/ui primitives
- Lucide icons

The frontend is not a Next.js app in this repository. The active implementation is the Vite client in `Frontend/`.

## Application Structure

### App entrypoints

- `Frontend/src/App.tsx`
  - wires the app through the error boundary, providers, and route tree
- `Frontend/src/app/AppProviders.tsx`
  - mounts `BrowserRouter`
  - mounts `QueryClientProvider`
  - mounts `AuthProvider`
  - mounts toast providers
- `Frontend/src/app/AppRoutes.tsx`
  - owns public and protected route registration
  - lazy-loads route components for route-level code splitting
- `Frontend/src/shared/layout/MainLayout.tsx`
  - shared authenticated shell
  - route-aware navigation
  - notifications summary in the shell

### Feature ownership

- `Frontend/src/features/marketing`
- `Frontend/src/features/auth`
- `Frontend/src/features/dashboard`
- `Frontend/src/features/assessment`
- `Frontend/src/features/roadmap`
- `Frontend/src/features/jobs`
- `Frontend/src/features/notifications`
- `Frontend/src/features/profile`
- `Frontend/src/features/settings`
- `Frontend/src/features/advisory`

### Shared presentation system

- `Frontend/src/index.css`
  - design tokens
  - font imports
  - atlas surfaces
  - poster surfaces
  - gradients, motion, and shared utility classes
- `Frontend/src/shared/components`
  - `PageShell`
  - `SectionHeader`
  - `StatePanel`
  - `JourneyProgress`
  - `ChoiceCard`
  - `PosterHero`

## Route Map

### Public routes

- `/`
- `/login`
- `/register`
- `/forgot-password`

### Protected routes

- `/dashboard`
- `/assessment`
- `/assessment/session/:assessmentId`
- `/assessment/results/:assessmentId`
- `/roadmap`
- `/advisor`
- `/jobs`
- `/jobs/saved`
- `/jobs/:jobId`
- `/notifications`
- `/profile`
- `/settings`

Protected routes are wrapped by `ProtectedRoute` and rendered inside `MainLayout`.

## Visual and UX Direction

The frontend now follows the "career atlas" direction defined in the feature spec:

- public and auth pages are poster-led and brand-forward,
- authenticated pages are calmer editorial surfaces,
- hierarchy is communicated through layout and type before cards,
- roadmap flows emphasize sequence and next action,
- assessments feel like guided quiz interactions,
- loading, empty, processing, and error states are intentional surfaces rather than raw placeholders.

## Performance Guardrails

The standing frontend performance reference is:

- `docs/product/FRONTEND_PERFORMANCE_REFERENCE.md`

That document is the source of truth for:

- keeping state local before introducing broader shared state,
- preferring TanStack Query for server state,
- protecting route-level code splitting,
- limiting scroll-time paint cost from blur and fixed-background effects,
- and keeping motion transform-led and accessibility-safe.

## API Client and Auth Behavior

`Frontend/src/lib/api.ts` is the authoritative frontend API layer.

### Current auth flow

- access and refresh tokens are stored in `localStorage` under `sha8lny_access_token` / `sha8lny_refresh_token`
- the client sends `Authorization: Bearer <token>`
- `401` responses trigger refresh through `/users/auth/refresh/`
- refresh failure clears stored tokens and redirects to `/login`

This is the current implementation, not the final ideal architecture. It works with the present backend, but a later hardening pass should move toward cookie-backed auth.

### Security trade-offs (documented for defense review)

| Topic | Current choice | Risk | Mitigation / future work |
|-------|----------------|------|--------------------------|
| Token storage | `localStorage` (readable by JS) | XSS can exfiltrate JWTs | Keep dependency surface small; avoid `dangerouslySetInnerHTML`; prefer httpOnly cookies in production |
| CSP | Not enforced by the SPA itself | Inline script injection harder to block at the edge | Production deploy should set a strict `Content-Security-Policy` on the static host (e.g. `default-src 'self'`; limit `connect-src` to API origin) |
| Password reset | Route stub only (`/forgot-password`) | Users may expect email recovery | Page states MVP limitation; no fake success path |
| Refresh rotation | Backend rotates + blacklists refresh tokens | Stolen refresh token window | Short access-token TTL (1 h) limits blast radius |

Server state in feature pages still uses local `useEffect` + `useState` fetch patterns. TanStack Query remains a dev dependency for test utilities only until a page adopts `useQuery`.

### Shared client conventions

- base URL: `import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"`
- all feature calls go through `api`, `apiClient`, and typed endpoint groups
- shared error surface: `ApiError` and `getApiErrorMessage`

## Backend Contract Expectations

### Users / profile

Frontend expects:

- `/users/me/`
- `/users/me/preferences/`
- `/users/user-skills/`
- `/users/skills/`

The profile contract now includes optional onboarding and preference-facing fields used by the redesigned profile/settings surfaces.

### Roadmaps

Frontend expects:

- `/roadmap/`
- `/roadmap/:id/`
- `/roadmap/:id/stats/`
- `/roadmap/:id/activate/`
- `/roadmap/:id/progress/`
- `/roadmap/templates/`

The reconstructed roadmap UI now relies on these added presentation fields:

- `presentation_mode`
- `current_focus_node_id`
- `journey_summary`
- `journey_nodes`
- milestone and phase `node_type`
- milestone and phase `estimated_effort`
- milestone and phase `next_action`
- stats `next_action`

### Assessments

Frontend expects:

- `/assessment/`
- `/assessment/:id/`
- `/assessment/:id/submit/`
- `/assessment/:id/result/`

The reconstructed assessment flow now relies on:

- question `interaction_mode`
- question `estimated_seconds`
- assessment `presentation`
- result `submission_state`
- result `status_message`
- result `next_actions`

The frontend handles async result states by treating HTTP `202` from the result endpoint as "still processing" and polling for completion.

### Jobs

Frontend expects:

- `/jobs/`
- `/jobs/search/`
- `/jobs/:id/`
- `/jobs/saved-jobs/`
- `/jobs/saved-jobs/toggle/:jobId/`

The jobs UI now uses these extra fields:

- `is_saved`
- `external_action_available`
- `skill_match_summary`

### Notifications

Frontend expects:

- `/notifications/notifications/`
- `/notifications/notifications/mark_all_read/`
- `/notifications/stats/`

The shell and notifications page now use:

- notification `time_ago`
- notification `display_type`
- notification `is_actionable`
- stats `nav_summary`

## Automated Validation

Validated on 2026-04-04 with:

```bash
cd Frontend && npm run build
cd Frontend && npm run test:run
cd Backend && ./venv/bin/python manage.py check
cd Backend && ./venv/bin/python -m pytest apps/roadmaps/tests/test_frontend_contracts.py apps/assessments/tests/test_frontend_contracts.py apps/jobs/tests/test_frontend_contracts.py apps/notifications/tests.py
```

Results:

- frontend build passed
- frontend tests passed: `9` files, `16` tests
- backend system check passed
- backend frontend-contract regression suite passed: `9` tests

## Remaining Follow-up

- Run manual browser review for the public/auth poster surfaces at desktop and mobile widths.
- Run manual browser review for roadmap density and the mobile sequential fallback.
- Consider replacing `localStorage` token handling with a hardened session strategy in a later auth pass.
