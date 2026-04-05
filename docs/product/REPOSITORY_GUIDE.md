# Repository Guide

## Purpose

This repository is split between active product code and archived reference material. Active work should stay focused on the runtime system, not presentation artifacts or historical research notes.

## Active Areas

- `Frontend/`: client application
- `Backend/`: Django API and application modules
- `ai-models/`: AI, retrieval, and model-serving support code
- `docs/product/`: current engineering and product documentation

## Archived Areas

- `archive/presentations/`: presentation decks and presentation-generation helpers
- `archive/thesis/`: thesis drafting and research reference material
- `archive/datasets/`: datasets kept for reference, not active runtime inputs

## Frontend Ownership Boundaries

- `src/app/`: global app shell, route registration, providers
- `src/features/<feature>/`: feature-owned routes, components, hooks, and local services
- `src/shared/`: cross-feature layout and truly shared building blocks
- `src/components/ui/`: reusable UI primitives only
- `src/lib/`: shared API and utility modules

## Branching Conventions

- `cleanup/<scope>`: repo cleanup, pruning, and archive moves
- `refactor/<scope>`: internal reorganization without product scope changes
- `fix/<scope>`: behavior or data-flow corrections
- `feature/<scope>`: net-new user-facing functionality

## Deletion Rules

- Delete automatically only when a file is clearly unused, duplicated, generated, or superseded.
- If runtime ownership or future product relevance is unclear, review before deleting.
- Prefer moving non-product material into `archive/` over permanent deletion.
