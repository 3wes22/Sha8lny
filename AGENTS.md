# Grad-Project Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-14

## Active Technologies
- Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend + Django 5, Django REST Framework, Celery, Redis cache/broker, Simple JWT, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library (002-ai-rag-experiment)
- Existing Django relational persistence with JSON-backed assessment payloads; Redis-backed cache and queue in base/production; SQLite remains acceptable in developmen (002-ai-rag-experiment)

- Frontend: TypeScript 5.8, React 18.3, Vite 5, React Router 6, TanStack Query 5, Tailwind CSS 3, Radix UI primitives, Vitest, Testing Library
- Backend: Python 3.13, Django 5.0, Django REST Framework, Simple JWT, drf-spectacular, pytest, Celery, Redis, PostgreSQL for production, SQLite for development
- AI stack: local Gemma 4 E4B via Ollama, deterministic Django service orchestration, ChromaDB vector store, sentence-transformers embeddings (`all-MiniLM-L6-v2`)
- Repository shape: full-stack monorepo with active code in `Frontend/`, `Backend/`, `ai-models/`, and current engineering docs in `docs/product/`

## Project Structure

```text
Frontend/
├── src/
│   ├── app/
│   ├── components/ui/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── shared/
│   └── test/
└── package.json

Backend/
├── apps/
│   ├── advisory/
│   ├── assessments/
│   ├── career_tools/
│   ├── core/
│   ├── courses/
│   ├── jobs/
│   ├── notifications/
│   ├── progress/
│   ├── roadmaps/
│   └── users/
├── config/
├── manage.py
├── pytest.ini
└── requirements.txt

ai-models/
├── src/
│   ├── assessment/
│   ├── llm/
│   ├── rag/
│   ├── recommendations/
│   ├── roadmap/
│   └── utils/
├── data/
├── tests/
└── requirements.txt

docs/product/
specs/
archive/
```

## Commands

- Frontend setup: `cd Frontend && npm install`
- Frontend dev: `cd Frontend && npm run dev`
- Frontend build: `cd Frontend && npm run build`
- Frontend tests: `cd Frontend && npm run test:run`
- Frontend lint: `cd Frontend && npm run lint`
- Backend setup: `cd Backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Backend migrations: `cd Backend && python manage.py migrate`
- Backend dev server: `cd Backend && python manage.py runserver`
- Backend checks: `cd Backend && python manage.py check`
- Backend tests: `cd Backend && pytest`
- Backend targeted contract validation: `cd Backend && pytest apps/roadmaps/tests/test_frontend_contracts.py apps/assessments/tests/test_frontend_contracts.py apps/jobs/tests/test_frontend_contracts.py apps/notifications/tests.py`
- AI setup: `cd ai-models && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- AI smoke tests: `cd ai-models && pytest`
- AI vector DB smoke test: `cd ai-models && python test_vector_db.py`

## Code Style

- Follow `docs/product/CODING_STANDARDS.md` for Python and Django conventions, including PEP 8-style naming, type hints, Google-style docstrings where useful, and service-layer separation.
- Keep frontend ownership boundaries intact: route and feature logic in `Frontend/src/features/*`, app shell in `Frontend/src/app`, cross-feature layout in `Frontend/src/shared`, reusable primitives in `Frontend/src/components/ui`, and shared API helpers in `Frontend/src/lib`.
- Use TanStack Query for server state, keep local UI state local, preserve route-level lazy loading, and avoid heavy fixed-background plus blur combinations on primary scrolling surfaces.
- Treat AI orchestration as deterministic backend workflow code, not agentic planning inside the product runtime.

## Recent Changes
- 002-ai-rag-experiment: Added Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend + Django 5, Django REST Framework, Celery, Redis cache/broker, Simple JWT, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library

- 001-frontend-visual-rebuild: Rebuilt the frontend around the career-atlas visual system, feature-first structure, lazy-loaded routes, shared authenticated shell, and contract-tested frontend/backend interfaces.
- 2026-04-07 architecture reset: Accepted `docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md` as the active AI architecture, replacing old OpenAI/Anthropic/LangChain/Pinecone assumptions with local Gemma via Ollama.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
