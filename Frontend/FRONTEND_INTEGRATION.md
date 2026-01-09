Frontend Integration Guide
==========================

Purpose
-------
- Explain how the React/Tailwind frontend is wired so backend engineers can expose the right endpoints and data shapes.
- Call out every screen that currently uses mock data or local state so you know where to plug APIs.
- Provide conventions for HTTP clients, auth handling, and environment config.

Quick Start
-----------
- Requirements: Node 18+.
- Install deps: `npm install`
- Run dev server: `npm run dev` (Vite defaults to http://localhost:5173)
- Build: `npm run build` ; Preview: `npm run preview`
- Lint: `npm run lint`
- Path alias: `@/*` -> `src/*` (see tsconfig.json)

Tech Stack & Conventions
------------------------
- React 18 + Vite + TypeScript.
- Routing: `react-router-dom` (BrowserRouter). Routes defined in `src/App.tsx`.
- Data fetching/caching: `@tanstack/react-query` provider already mounted in `App.tsx`.
- UI: shadcn/ui + Tailwind (`src/components/ui/*`), Radix primitives, lucide icons.
- Toasts: `useToast` (`src/hooks/use-toast`) renders through `<Toaster />` and `<Sonner />` in `App.tsx`.
- Styling helpers: `cn` util (`src/lib/utils.ts`) and Tailwind design tokens.

Project Layout (high value folders)
-----------------------------------
- `src/main.tsx` mounts React root.
- `src/App.tsx` sets providers and route map.
- `src/components/layout/MainLayout.tsx` shared shell for authenticated pages (top nav, mobile menu).
- `src/components/ui/*` generated shadcn primitives.
- `src/components/Roadmap/*` roadmap-specific UI building blocks.
- `src/data/tracks.ts` static learning-track dataset used by Roadmap page; replace with API once available.
- `src/hooks/use-toast.ts` toast hook.
- `src/pages/*` one file per route (see routing map below).

Routing Map & Guards
--------------------
- Public: `/` (Index), `/login`, `/register`, wildcard `*` -> `NotFound`.
- Auth-required shell: all other routes render inside `MainLayout` (`/dashboard`, `/profile`, `/assessment`, `/assessment/session`, `/assessment/results`, `/roadmap`, `/advisor`, `/jobs`, `/jobs/saved`, `/settings`).
- There is **no auth guard yet**. To enforce auth, add a wrapper around protected `<Route>` elements or a layout-level redirect using your auth state/token.

Data & API Integration Points (screen-by-screen)
------------------------------------------------
- Auth (`src/pages/Login.tsx`, `Register.tsx`): currently simulate success with `setTimeout`. Replace submit handlers with real `POST /auth/login` and `POST /auth/register`, then store tokens (context or React Query `queryClient.setQueryData`) and redirect. Decide storage (httpOnly cookies vs. localStorage) with backend.
- Dashboard (`src/pages/Dashboard.tsx`): all stats/milestones are hard-coded. Swap with queries such as `GET /me/overview` returning progress %, streak, recent milestones, upcoming milestones.
- Profile (`src/pages/Profile.tsx`): form state is local; `completionPercentage` is a stub. On load, fetch `GET /me/profile`; on save, `PUT /me/profile`. Skills add/remove currently mutate local state; mirror backend response to keep tags in sync.
- Assessment selection (`src/pages/Assessment.tsx`): career paths list is mocked. Ideally driven by `GET /assessments/paths` supporting search.
- Assessment session (`src/pages/AssessmentSession.tsx`): questions array is local, scoring is front-end only, and submission just navigates with `location.state`. Replace with:
  - Fetch questions: `GET /assessments/:pathId/questions`.
  - Submit: `POST /assessments/:pathId/responses` with answers; backend returns score/level/resultId.
  - Navigate to results using returned result ID or refetch.
- Assessment results (`src/pages/AssessmentResults.tsx`): reads answers from navigation state; shows fallback if missing. Prefer loading by ID: `GET /assessments/results/:resultId` so a hard refresh works.
- Roadmap (`src/pages/Roadmap.tsx` + `src/data/tracks.ts`): currently renders static `TRACKS` data. Replace with `GET /roadmap` (or per-track `GET /tracks/:id`) and remove static file once API is ready.
- Advisor (`src/pages/Advisor.tsx`): chat is simulated with `setTimeout`. Integrate with your AI/chat endpoint (`POST /advisor/chat` or streaming SSE/WebSocket). Maintain `messages` array and handle typing indicator from stream events.
- Jobs & Saved Jobs (`src/pages/Jobs.tsx`, `SavedJobs.tsx`):
  - Job list is mocked (`ALL_JOBS`); add `useQuery` to fetch `GET /jobs?query=...&filters...`.
  - `MOCK_ASSESSMENT` drives “Why this job?” copy; replace with the latest assessment summary from API.
  - Saved jobs persist in `localStorage` (`sha8alny_saved_jobs`). If backend support exists, sync via `POST /me/saved-jobs` and `GET /me/saved-jobs`.
- Settings (`src/pages/Settings.tsx`): account info, notifications, and password change are local-only. Wire to `GET/PUT /me`, `PUT /me/password`, and `PUT /me/notifications`. Danger zone (delete account) is UI-only.
- Index/Marketing (`src/pages/Index.tsx`): static landing page; only needs minor analytics integrations.

State, Persistence, and Side Effects
------------------------------------
- React Query provider is ready; prefer `useQuery`/`useMutation` over manual `useEffect` for API calls.
- Navigation side effects use `react-router-dom`’s `useNavigate` and `Link`. Keep redirects in submit success callbacks.
- Local persistence: only saved jobs use `localStorage`. Everything else is ephemeral unless you add API calls.
- Toasts are the standard feedback channel; reuse `useToast` in mutations for success/error states.

Recommended API Client Pattern
------------------------------
- Add a small fetch wrapper (e.g., `src/lib/api.ts`) that injects `VITE_API_BASE_URL`, auth headers, and parses JSON.
- Example (simplified):
```ts
// src/lib/api.ts
const API_URL = import.meta.env.VITE_API_BASE_URL;

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}
```
- With React Query:
```ts
const { data, isLoading } = useQuery({
  queryKey: ["jobs", filters],
  queryFn: () => api<Job[]>("/jobs?" + new URLSearchParams(filters)),
});
```

Env & Configuration
-------------------
- Add `VITE_API_BASE_URL` in `.env` (Vite exposes vars prefixed with `VITE_`).
- If using auth cookies, ensure dev server and API share origin or set proper CORS/credentials.
- Tailwind config: `tailwind.config.ts`; typography plugin is enabled.

Integration Checklist
---------------------
- [ ] Decide auth strategy (cookie vs. bearer), implement storage, and gate protected routes.
- [ ] Replace mock datasets (Dashboard, Assessment, Roadmap, Jobs, Advisor) with API queries/mutations.
- [ ] Persist profile, settings, password change, and notification preferences.
- [ ] Provide assessment result endpoint to support refresh-safe results page.
- [ ] Align backend response shapes with UI expectations (see per-page notes); return consistent IDs for navigation (e.g., assessment `resultId`, job `id`).
- [ ] Update error/loading states once API wiring is in place (spinners/placeholders as needed).
