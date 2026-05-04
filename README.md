# Sha8alny

Sha8alny is an AI-powered career development platform focused on the Egyptian job market. The active product code lives in three main work areas:

- `Frontend/`: React 18 + Vite + TypeScript client
- `Backend/`: Django REST Framework modular monolith
- `ai-models/`: AI and RAG support code

The frontend has been rebuilt around a feature-first structure and a new "career atlas" visual system. Public and auth surfaces now use poster-style layouts, authenticated flows share a unified atlas shell, and route-level code splitting is enabled through lazy-loaded route entrypoints.

## Current Repository Layout

```text
Grad-Project/
├── Backend/                  # Active backend code
├── Frontend/                 # Active frontend code
├── ai-models/                # Active AI code
├── docs/
│   └── product/              # Current product documentation
├── archive/                  # Presentations, thesis material, reference datasets
├── CLAUDE.md
└── README.md
```

## Frontend Structure

The frontend is organized by feature. Route entrypoints are thin; shared layout, primitives, and API contracts live outside feature folders.

```text
Frontend/src/
├── app/                      # Providers, route map, error boundary
├── features/
│   ├── advisory/
│   ├── assessment/
│   ├── auth/
│   ├── dashboard/
│   ├── jobs/
│   ├── marketing/
│   ├── notifications/
│   ├── profile/
│   ├── roadmap/
│   └── settings/
├── shared/
│   ├── components/
│   └── layout/
├── components/ui/            # Shared shadcn-style UI primitives
├── hooks/
├── lib/                      # Typed API client and helpers
└── test/
```

## Current Frontend Highlights

- `Frontend/src/app/AppProviders.tsx`: Browser router, React Query, auth provider, toaster providers.
- `Frontend/src/app/AppRoutes.tsx`: lazy-loaded public and protected routes.
- `Frontend/src/shared/layout/MainLayout.tsx`: shared authenticated shell with route-aware navigation and notifications summary.
- `Frontend/src/lib/api.ts`: typed REST client with token refresh, shared error handling, and feature contracts.
- `Frontend/src/index.css`: editorial design tokens, type system, atlas surfaces, gradients, and motion helpers.

## Validation Status

The visual reconstruction and contract upgrade were validated on April 4, 2026 with:

- `cd Frontend && npm run build`
- `cd Frontend && npm run test:run`
- `cd Backend && ./venv/bin/python manage.py check`
- `cd Backend && ./venv/bin/python -m pytest apps/roadmaps/tests/test_frontend_contracts.py apps/assessments/tests/test_frontend_contracts.py apps/jobs/tests/test_frontend_contracts.py apps/notifications/tests.py`

All four command groups passed.

## Documentation

Current product documentation is under `docs/product/`:

- `docs/product/ARCHITECTURE.md`
- `docs/product/FRONTEND_INTEGRATION.md`
- `docs/product/FRONTEND_PERFORMANCE_REFERENCE.md`
- `docs/product/SRS.md`
- `docs/product/TECH_STACK.md`
- `docs/product/DATABASE_SCHEMA.md`

Feature planning and task artifacts for the frontend rebuild are under `specs/001-frontend-visual-rebuild/`.

Archived presentation material, thesis notes, and reference datasets are under `archive/`.

## Development Workflow

Recommended branch naming:

- `cleanup/...` for repo cleanup and structural work
- `refactor/...` for non-trivial internal improvements
- `fix/...` for behavior bugs and contract repairs
- `feature/...` for net-new product features

Keep backend contract changes isolated from visual redesign work whenever possible.

## Getting Started

### Backend

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set GEMINI_API_KEY in Backend/.env
python3 manage.py migrate
python3 manage.py seed_graduation_demo --reset
python3 manage.py runserver
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

### AI Models

```bash
cd ai-models
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The default inference path now uses the hosted Gemini API. For backend and `ai-models` flows, configure `GEMINI_API_KEY` before running generation features.

For the evaluator-ready demo flow and reset steps, use [GRADUATION_DEMO_RUNBOOK.md](docs/product/GRADUATION_DEMO_RUNBOOK.md).
