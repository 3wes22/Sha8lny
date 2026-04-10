# Quickstart: Sha8alny Frontend Visual Reconstruction

## 1. Start the stack

### Backend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
python manage.py runserver
```

### Frontend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Frontend
npm install
npm run dev
```

## 2. Core verification commands

### Frontend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Frontend
npm run build
npm run test:run
```

### Backend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
python manage.py check
```

## 3. Manual acceptance walkthrough

### Public flow

1. Open `/`
2. Confirm the landing experience reflects the new visual direction.
3. Open `/login` and `/register`.
4. Confirm the auth surfaces feel aligned with the rest of the product.

### Core authenticated flow

1. Sign in and land on `/dashboard`.
2. Confirm the main navigation shell is stable and readable.
3. Open `/roadmap` and verify hierarchy, progress emphasis, and next-step clarity.
4. Open `/assessment`, progress into `/assessment/session/:assessmentId`, and confirm quiz-style guidance.
5. Open `/assessment/results/:assessmentId` and confirm clear processing or results messaging.
6. Open `/jobs`, `/jobs/saved`, and `/jobs/:jobId`; verify consistent save/apply behavior.
7. Open `/notifications`, `/profile`, `/settings`, and `/advisor`; confirm shared layout consistency.

## 4. Responsive checks

1. Test at desktop width and confirm roadmap/atlas density is readable.
2. Test at mobile width and confirm roadmap-heavy content collapses into a sequential form.
3. Confirm action buttons and progress indicators remain usable at smaller breakpoints.

## 5. Feature-specific review checklist

- The first public viewport feels branded and intentional rather than like a boxed SaaS hero.
- The roadmap experience feels closer to a learning journey than a static dashboard.
- Assessment screens feel like professional guided interactions rather than plain forms.
- Logged-in screens rely on layout and typography more than dashboard-card mosaics.
- Motion is noticeable in the hero or journey transitions, but does not distract from task completion.
- No primary navigation route is broken or placeholder-only.
- Processing, empty, and error states are visually intentional.
- The selected Genially direction is visible in the assessment/onboarding interaction style without making the product feel toy-like.

## 6. Validation log

### Automated validation completed on 2026-04-04

- `Frontend`: `npm run build` passed.
- `Frontend`: `npm run test:run` passed with `9` test files and `16` tests.
- `Backend`: `python manage.py check` passed.
- `Backend`: frontend-contract regression suite passed:
  - `apps/roadmaps/tests/test_frontend_contracts.py`
  - `apps/assessments/tests/test_frontend_contracts.py`
  - `apps/jobs/tests/test_frontend_contracts.py`
  - `apps/notifications/tests.py`

### Notes from the automated pass

- Route-level lazy loading is active and the frontend now builds as split chunks instead of a single large route bundle.
- Shared shell, dashboard, roadmap, assessment, jobs, notifications, and auth route regressions are covered by frontend tests.
- Backend responses now expose the presentation metadata the rebuilt frontend expects for roadmaps, assessments, jobs, and notifications.

### Remaining manual browser review

- Review landing, login, and register surfaces at desktop and mobile widths for final visual polish.
- Review roadmap density and mobile sequential fallback in a real browser.
- Review assessment transitions, loading states, and result hierarchy in a real browser session.
- Review cross-route consistency for `/jobs`, `/jobs/saved`, `/jobs/:jobId`, `/notifications`, `/profile`, `/settings`, and `/advisor`.
