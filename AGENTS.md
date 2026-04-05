# Grad-Project Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-04

## Active Technologies

- TypeScript 5.8 on React 18.3 frontend; Python 3.13 backend support for contract changes + React Router 6, TanStack Query 5, Tailwind CSS 3, Radix UI primitives, Django REST Framework (001-frontend-visual-rebuild)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

TypeScript 5.8 on React 18.3 frontend; Python 3.13 backend support for contract changes: Follow standard conventions

## Recent Changes

- 001-frontend-visual-rebuild: Added TypeScript 5.8 on React 18.3 frontend; Python 3.13 backend support for contract changes + React Router 6, TanStack Query 5, Tailwind CSS 3, Radix UI primitives, Django REST Framework

<!-- MANUAL ADDITIONS START -->
- Frontend performance reference: `docs/product/FRONTEND_PERFORMANCE_REFERENCE.md`
- Performance defaults for this repo: keep state local, use TanStack Query for server data, prefer route-level lazy loading, and avoid fixed-background plus heavy-blur combinations on primary scrolling surfaces.
<!-- MANUAL ADDITIONS END -->
