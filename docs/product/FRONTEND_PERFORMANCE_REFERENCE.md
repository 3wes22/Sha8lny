# Frontend Performance Reference

## Purpose

This document captures the frontend performance rules that should stay in project context during ongoing Sha8alny work.

## Primary External Reference

- Source: Strapi, [React & Next.js in 2025 - Modern Best Practices](https://strapi.io/blog/react-and-nextjs-in-2025-modern-best-practices)
- Published: June 6, 2025
- Last updated on page: June 12, 2025

## Interpretation for This Repository

The Strapi article is partly Next.js-oriented, but the main guidance still applies to this repository because the active frontend is a React 18 + Vite + TypeScript application.

The repo should adopt the principles, not the framework-specific APIs:

- keep state close to the component that uses it,
- prefer TanStack Query for server state and caching,
- reduce client bundle size before adding new client-side libraries,
- lazy-load route surfaces and heavy features,
- optimize rendering and paint cost, not only JavaScript logic,
- treat accessibility and maintainability as part of performance work.

## Standing Project Rules

### 1. Keep State Local First

- Do not move state higher in the tree unless multiple distant consumers actually need it.
- Prefer `useState`, `useReducer`, and feature-local hooks before introducing wider shared state.
- Avoid adding global state libraries for data that already belongs in query caching or route state.

### 2. Use TanStack Query for Server State

- API-backed lists, detail views, polling, and cache invalidation belong in TanStack Query.
- Do not duplicate server data in ad hoc client stores unless there is a measured reason.
- Favor invalidation and cache reuse over manual fetch chains.

### 3. Keep the Client Bundle Small

- Lazy-load route entrypoints and heavy feature modules.
- Avoid adding third-party packages for work the current stack already handles.
- Import directly instead of through large barrel patterns when practical.

### 4. Reduce Scroll-Time Paint Cost

- Avoid `background-attachment: fixed` on primary scrolling surfaces.
- Avoid large blurred decorative layers on persistent layouts.
- Use `backdrop-filter` sparingly and prefer lower blur strengths on always-visible shells.
- Prefer gradients and composited layers over huge filter-based glow effects.
- Use `content-visibility: auto` on below-the-fold sections when layout allows it.

### 5. Animate Cheap Properties

- Prefer `transform` and `opacity` for transitions and entrance motion.
- Keep hover motion short, subtle, and consistent.
- Avoid layout-affecting animation where a transform-based cue is enough.
- Use reduced-motion fallbacks for non-essential motion.

### 6. Measure Before Memoizing

- Do not scatter `useMemo` and `useCallback` defensively.
- Memoize only when profiling or repeated heavy work shows a real benefit.
- Derived view data that is cheap to compute should stay simple.

### 7. Accessibility Is Part of the Performance Budget

- Use semantic HTML first.
- Preserve visible focus states.
- Keep contrast strong on glass, gradient, and poster surfaces.
- Prefer links for navigation and buttons for actions.

### 8. Maintainability Prevents Performance Regressions

- Document major frontend architecture decisions as they are made.
- Keep route ownership and shared UI primitives explicit.
- Add regression tests for critical route and state behavior.

## Next.js-Specific Guidance to Keep in Mind for Future Migration

These are not active implementation rules in the current Vite app, but they should stay on the table if the frontend migrates later:

- use hybrid rendering instead of making everything client-rendered,
- fetch on the server for first load when appropriate,
- use Suspense boundaries to avoid blocking the full page,
- stream data where the framework supports it,
- use framework image optimization instead of raw image tags.

## Current Repo Performance Checklist

Before shipping major frontend visual changes:

1. Check that scrolling remains smooth on the authenticated shell.
2. Check that no new always-visible section relies on heavy blur or fixed-background paint work.
3. Check that route-level code splitting still works.
4. Check that interactive transitions use transform/opacity-led motion.
5. Check that added state is local or query-backed by default.
6. Check that the change did not silently weaken contrast or focus visibility.
