# Legacy Branches Documentation

This document records all branches that existed before the repository consolidation on 2026-01-10.

All legacy code is preserved via git tags with the `legacy/` prefix.

## How to Access Legacy Code

```bash
# List all legacy tags
git tag -l 'legacy/*'

# Checkout a specific legacy branch
git checkout legacy/Backend        # Django backend (Jan 8, 2026)
git checkout legacy/Frontend_LastUpdates  # React frontend ZIP (Dec 27, 2025)
git checkout legacy/ai-models      # ML infrastructure (Dec 7, 2025)
git checkout legacy/3wes-changes   # Old frontend wireframes (Nov 4, 2025)
git checkout legacy/Doc-hub        # ERD diagrams (Nov 9, 2025)
git checkout legacy/frontendUPDATES  # Incomplete frontend (Dec 17, 2025)
git checkout legacy/frontend       # Empty branch (Oct 27, 2025)
git checkout legacy/main           # Original main (Oct 27, 2025)
```

## Branch History Summary

| Branch | Last Updated | Content | Status After Consolidation |
|--------|--------------|---------|---------------------------|
| `Backend` | 2026-01-08 | Django backend with 9 modules, all API layers | Merged to main |
| `Frontend_LastUpdates` | 2025-12-27 | Complete React frontend (ZIP file) | Extracted & merged to main |
| `ai-models` | 2025-12-07 | ML/AI infrastructure | Merged to main |
| `Doc-hub` | 2025-11-09 | ERD diagrams | Merged to docs/ |
| `3wes-changes` | 2025-11-04 | Old frontend wireframes + backend docs | Superseded |
| `frontendUPDATES` | 2025-12-17 | Incomplete upload (config only) | Deleted |
| `frontend` | 2025-10-27 | Empty (same as main) | Deleted |
| `main` | 2025-10-27 | Initial PRD only | Replaced with consolidated code |

## Detailed Branch Contents

### Backend (legacy/Backend)
- Django REST framework backend
- 9 app modules: users, courses, assessments, roadmaps, progress, jobs, advisory, career_tools, notifications
- Complete service and API layers
- Database models and migrations

### Frontend_LastUpdates (legacy/Frontend_LastUpdates)
- Contains `Frontend_Graduation_Project.zip`
- React 18 + Vite + TypeScript frontend
- 14 pages: Dashboard, Profile, Assessment, Jobs, Advisor, Roadmap, Settings, etc.
- shadcn/ui components
- FRONTEND_INTEGRATION.md with API integration guide

### ai-models (legacy/ai-models)
- ML infrastructure setup
- LLM inference modules
- RAG (Retrieval Augmented Generation) setup
- Recommendation system placeholders

### 3wes-changes (legacy/3wes-changes)
- Early frontend wireframes (superseded by Frontend_LastUpdates)
- Backend architecture documentation (moved to docs/)
- API specification drafts

### Doc-hub (legacy/Doc-hub)
- ERD diagrams (ERD.svg, ERD.jpg)
- Visual Paradigm project files

---

*This file was created during repository consolidation on 2026-01-10*
