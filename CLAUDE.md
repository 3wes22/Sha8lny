# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sha8lny** (also spelled Sha8alny) is an AI-powered career empowerment platform targeting the Egyptian job market. The platform provides personalized career guidance through AI-driven assessments, adaptive learning pathways, job matching, and career advisory.

**Current Status**: Phases 0-5 Complete (full Gemini AI integration across Assessment, Roadmap, Jobs, and Advisory modules)
**Implementation Approach**: Hosted demo runtime on Gemini API (default), with an optional local Ollama fallback. See `docs/product/ADR-002-HOSTED-DEMO-AI-RUNTIME.md`.

## Project Architecture

This is a **full-stack monorepo** with three main components:

```
Grad-Project/
├── Backend/         # Django REST API (Modular Monolith)
├── Frontend/        # React + TypeScript + Vite
├── ai-models/       # Custom ML models (future integration)
└── docs/            # Documentation
```

### Backend (Django)
- **Architecture**: Modular Monolith with service layer pattern
- **Database**: PostgreSQL (Production), SQLite (Development)
- **API**: Django REST Framework with JWT authentication
- **Background Tasks**: Celery + Redis (configured, not yet used)
- **Real-time**: Django Channels (configured, not yet used)

### Frontend (React + TypeScript)
- **Framework**: React 18 + TypeScript + Vite
- **UI**: shadcn/ui components + Tailwind CSS
- **Routing**: React Router v6
- **State**: React Query + Context API
- **Auth**: JWT tokens with automatic refresh

### AI Models (Future)
- **Approach**: Local LLM via Ollama (llama3.2, mistral)
- **No API costs**: Self-hosted models, offline-capable
- **Integration**: Phase 6 of implementation plan

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Access at: http://localhost:8000
Admin panel: http://localhost:8000/admin/
API docs: http://localhost:8000/api/schema/swagger-ui/

### Frontend Setup
```bash
cd Frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
# Edit .env to point to backend (default: http://localhost:8000)

# Start development server
npm run dev
```

Access at: http://localhost:5173

### Running Tests

**Backend**:
```bash
cd Backend
pytest                          # Run all tests
pytest apps/assessments/        # Run specific app tests
pytest --cov=apps               # With coverage
```

**Frontend**:
```bash
cd Frontend
npm run build                   # Verify build works
```

## Current Implementation Status

### ✅ Phase 1: Foundation Stabilization (Complete)
- Testing infrastructure (pytest, fixtures)
- User authentication end-to-end (Auth0 + JWT)
- Profile management (update, save)
- User skills CRUD
- Settings persistence
- **Tests**: 51 passing (users module)

### ✅ Phase 2: Assessment Module Integration (Complete)
- Backend assessment CRUD endpoints
- Predefined assessment questions (6 questions: multiple_choice, scale, text)
- Assessment submission and response storage
- MVP scoring logic (immediate results, no AI yet)
- Frontend assessment flow:
  - Career path selection
  - Question answering session
  - Results display with recommendations
- **Tests**: 16 passing (assessment module), 67 total
- **Files Modified/Created**: 10 files across Backend and Frontend

### 🔄 Phase 3: Roadmap Module Integration (Next)
- Roadmap template seeding
- Roadmap CRUD working end-to-end
- Phase/Milestone progress updates
- Frontend roadmap display

### 📋 Phases 4-7: Remaining MVP Work
- Phase 4: Jobs Module Integration
- Phase 5: Advisory Module Integration
- Phase 6: AI/LLM Integration (Ollama)
- Phase 7: Progress & Dashboard

### 📋 Post-MVP Phases (Deferred)
- Phase 8: Notifications System
- Phase 9: Career Tools (Resume, Portfolio)
- Phase 10: DevOps & Production

**Full Implementation Plan**: See `.claude/plans/serialized-painting-quill.md`

## Module Structure

### Backend Apps

All apps follow the same structure:
```
apps/<module>/
├── models.py           # Database models (inherit from BaseModel)
├── serializers.py      # DRF serializers
├── views.py            # API viewsets
├── services.py         # Business logic (optional)
├── urls.py             # URL routing
├── admin.py            # Admin configuration
├── tasks.py            # Celery tasks (optional)
├── tests/              # Test suite
│   ├── test_api.py     # API endpoint tests
│   ├── test_models.py  # Model tests
│   └── test_services.py # Service tests
└── migrations/         # Database migrations
```

**Apps**:
- `core` - Base models, exceptions, utilities
- `users` - Authentication, profiles, skills (✅ Phase 1 complete)
- `assessments` - AI assessments (✅ Phase 2 complete)
- `roadmaps` - Learning roadmaps (🔄 Phase 3 next)
- `courses` - Course aggregation (Phase 4)
- `jobs` - Job scraping & matching (Phase 4)
- `advisory` - AI chatbot (Phase 5)
- `progress` - Progress tracking (Phase 7)
- `career_tools` - Resume/Portfolio (Phase 9)
- `notifications` - Notifications (Phase 8)

### Frontend Pages

**Completed**:
- `/login` - User login
- `/register` - User registration
- `/dashboard` - User dashboard (partially working)
- `/profile` - User profile management (✅)
- `/settings` - Settings (✅)
- `/assessment` - Career path selection (✅ Phase 2)
- `/assessment/session/:assessmentId` - Assessment taking (✅ Phase 2)
- `/assessment/results/:assessmentId` - Results display (✅ Phase 2)

**Wired to real backend APIs** (no longer mock data):
- `/roadmap` - Learning roadmap (AI-generated from assessment, with deterministic fallback)
- `/jobs` - Job search (skill-matched + LightGBM ranking)
- `/jobs/saved` - Saved jobs
- `/advisor` - AI career advisor (Gemini-backed, RAG-grounded)

## Development Workflows

### Making Changes to Models

```bash
cd Backend

# Make changes to models.py
# Then create and apply migrations
python manage.py makemigrations <app_name>
python manage.py migrate

# Test in Django shell
python manage.py shell
```

### Adding New API Endpoints

1. **Backend**:
   - Add method to `apps/<module>/views.py`
   - Add tests to `apps/<module>/tests/test_api.py`
   - Run tests: `pytest apps/<module>/`

2. **Frontend**:
   - Add TypeScript types to `src/lib/api.ts`
   - Add API method to appropriate `*Api` object
   - Use in components with error handling

### Running Backend and Frontend Together

**Terminal 1** (Backend):
```bash
cd Backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2** (Frontend):
```bash
cd Frontend
npm run dev
```

Access frontend at http://localhost:5173, which connects to backend at http://localhost:8000

## Testing Strategy

### Backend Tests (pytest)
- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test API endpoints with database
- **Coverage target**: >80% for critical paths

Run tests:
```bash
cd Backend
pytest                           # All tests
pytest apps/assessments/         # Specific module
pytest -v                        # Verbose
pytest --cov=apps --cov-report=html  # Coverage report
```

### Frontend Tests (Future)
- Currently: Manual testing + build verification
- Planned: Vitest + React Testing Library

## Key Technical Decisions

### 1. Modular Monolith (Not Microservices)
- Single Django app with module boundaries
- Direct Python imports between modules
- ACID transactions across modules
- Can extract to microservices later if needed

### 2. MVP Approach
- Predefined assessment questions (Phase 2)
- Immediate scoring without AI (Phase 2)
- AI integration deferred to Phase 6
- Local LLM (Ollama) when ready - no API costs

### 3. URL-based Navigation
- Assessment session: `/assessment/session/:assessmentId`
- Results: `/assessment/results/:assessmentId`
- RESTful resource identification

### 4. Soft Delete Pattern
- All models inherit from `BaseModel`
- `is_deleted` flag for logical deletion
- `deleted_at` timestamp
- Dual managers: `objects` (active) and `all_objects` (all)

## Component-Specific Documentation

For detailed component-specific information:

- **Backend Django**: See `Backend/CLAUDE.md`
  - Model patterns, admin configuration
  - Service layer architecture
  - Testing conventions
  - Database schema

- **AI Models**: See `ai-models/CLAUDE.md`
  - Custom ML implementations
  - Model training and deployment
  - LLM fine-tuning approach

## Common Commands Reference

### Backend
```bash
# Database
python manage.py migrate
python manage.py makemigrations <app>
python manage.py createsuperuser

# Testing
pytest
pytest apps/<app>/tests/
pytest --cov=apps

# Code Quality
black apps/
flake8 apps/
isort apps/

# Django Shell
python manage.py shell
```

### Frontend
```bash
# Development
npm run dev              # Start dev server
npm run build            # Production build
npm run preview          # Preview production build

# Linting
npm run lint
```

## Important Files & Directories

- `.claude/plans/` - Implementation phase plans
- `Backend/db.sqlite3` - Development database
- `Backend/.env` - Backend environment variables
- `Frontend/.env` - Frontend environment variables
- `Backend/conftest.py` - Pytest configuration and fixtures
- `Backend/apps/core/models.py` - BaseModel definition
- `Frontend/src/lib/api.ts` - API client and type definitions

## Module Status (as of current branch)

| Area | Status |
|---|---|
| Users / Auth (JWT + Auth0) | ✅ Working, well-tested |
| Assessments (staged AI, 8 roles, RAG corpus; **weighted** formative scoring) | ✅ Working, strongest coverage |
| Roadmaps (AI generation + deterministic fallback; O*NET = backend-only PoC) | ✅ Working |
| Jobs (search, skill match, LightGBM **weak-supervision** ranker + eval, ingest) | ✅ Working |
| Advisory (Gemini chat, RAG-grounded) | ✅ Working; light test coverage |
| Progress | 🟡 Working; light test coverage |
| Notifications | 🟡 Models/API/signals; email/push stubbed |
| Career Tools (resume/portfolio) | 🟡 CRUD works; generate/ATS return structured responses, PDF export is v2 |
| Courses (embedding search) | 🟡 Built; route wired at `config/urls.py`, matcher runs during roadmap generation |

Backend test suite: **274 tests passing**. Frontend builds clean.

## Current Known Issues

1. **Notifications delivery stubbed**: email/push sending not implemented (signals/models exist)
2. **Career Tools PDF/DOCX export**: deferred to v2 (endpoints return structured JSON, not a file)
3. **No Error Boundaries**: Frontend could add React error boundaries
4. **Celery present but optional**: AI tasks can run async; demo path runs them in-request
5. **roadmap.sh content license**: the vendored `ai-models/data/roadmap-sh-data/` is under a personal-use-only license (no redistribution). Treat as development-only; see `ai-models/data/CITATIONS.md` for the required pre-publication fix.
6. **Job ranker is a weak-supervision demonstrator**: trained on synthetic fixture postings with pseudo-labels, evaluated by leave-one-group-out NDCG/MAP vs. baselines (`ai-models/models/custom/EVAL_REPORT.md`). Real labeled market data is future work.

## Getting Help

- Check component-specific CLAUDE.md files for detailed guidance
- Implementation plan: `.claude/plans/serialized-painting-quill.md`
- Backend README: `Backend/README.md`
- Project documentation: `docs/` directory

## Phase Completion Checklist

When completing a phase:
- [ ] All deliverables implemented
- [ ] Tests written and passing
- [ ] No regression in existing tests
- [ ] Frontend builds successfully
- [ ] Manual verification of end-to-end flow
- [ ] Phase completion report written
- [ ] CLAUDE.md files updated

---

**Last Updated**: Phases 0-5 complete (Gemini AI integration across all core modules)
**Current Branch Focus**: `005-scenario-rag-corpus` - role-aware scenario retrieval for assessment question generation
