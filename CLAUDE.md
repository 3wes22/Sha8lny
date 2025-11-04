# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SkillPath AI** is a comprehensive educational platform for skill assessment, learning, and career development. Built as a graduation project, it features AI-driven assessments, personalized learning paths, job marketplace integration, and corporate training solutions. The platform is bilingual (English/Arabic) and targets the Egyptian job market.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Routing**: React Router DOM v6
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS with custom design tokens
- **State Management**: TanStack Query (React Query)
- **Form Handling**: React Hook Form + Zod validation
- **Code Editor**: Monaco Editor
- **Drag & Drop**: dnd-kit
- **Charts**: Recharts
- **Linting**: ESLint with TypeScript support

## Development Commands

### Essential Commands
```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:8080)
npm run dev

# Build for production
npm run build

# Build in development mode (useful for debugging)
npm run build:dev

# Lint all files
npm run lint

# Preview production build
npm run preview
```

### Notes
- Development server runs on port **8080** (not the Vite default of 5173)
- TypeScript strict mode is **disabled** (noImplicitAny, strictNullChecks are false)
- ESLint ignores unused variables and parameters by configuration

## Architecture Overview

### Routing Structure
The application uses a flat routing structure with the following main routes:
- `/` - Landing page (marketing/hero)
- `/register` - User registration
- `/login` - User authentication
- `/onboarding` - Multi-step onboarding flow
- `/dashboard` - Main user dashboard (stats, quick actions, progress)
- `/learning` - Learning hub with courses
- `/jobs` - Job marketplace
- `/assessments` - Assessment center (browse available assessments)
- `/take-assessment` - Interactive assessment experience
- `/profile` - User profile and settings
- `/corporate` - Corporate/B2B solutions

**IMPORTANT**: All custom routes MUST be added above the catch-all `*` route in `src/App.tsx:39`

### Component Organization

```
src/
├── pages/              # Route-level page components (12 pages)
├── components/
│   ├── assessment/     # Assessment-specific components
│   │   ├── questions/  # Question type components (CodeEditor, DragDropRanking, etc.)
│   │   └── ...         # Assessment flow components (Header, Sidebar, Navigation)
│   ├── ui/             # shadcn/ui components (51 components)
│   └── ...             # Shared components (Navigation, Footer, StatCard)
├── data/               # Static data and mock data (assessmentData.ts)
├── hooks/              # Custom React hooks (use-toast, use-mobile)
└── lib/                # Utilities (utils.ts for cn() helper)
```

### Assessment System Architecture

The assessment system is the core feature of the application:

**Data Structure** (`src/data/assessmentData.ts`):
- `Category` - Groups questions by topic (Technical Skills, Soft Skills, Language, Industry)
- `Question` - Supports 5 types: multiple-choice, slider, code, drag-drop, text
- Each category has status tracking: completed | in-progress | not-started | locked
- Questions support bilingual content (English/Arabic)

**Assessment Flow** (`src/pages/TakeAssessment.tsx`):
- State management for current category/question, answers, timer, gamification (XP/streaks)
- Auto-save functionality (every 30 seconds)
- Pause/resume capability
- Language switching (en/ar)
- Progress tracking across all categories
- Achievement system with notifications

**Question Components** (`src/components/assessment/questions/`):
- `MultipleChoice.tsx` - Radio button questions
- `SliderQuestion.tsx` - Rating scale questions (1-10)
- `CodeEditor.tsx` - Monaco-based code challenges with test cases
- `DragDropRanking.tsx` - Sortable items using dnd-kit
- `TextQuestion.tsx` - Free-form text responses

### Styling System

Tailwind configuration includes:
- Custom HSL-based color system (primary, secondary, accent, sidebar variants)
- CSS variables for gradients and shadows (defined in `src/index.css`)
- Dark mode support via class strategy
- Custom animations: accordion-down, accordion-up, scale-in, slide-in-top
- Extended color palette for primary-light, primary-dark, secondary-light, accent-light

**Path Alias**: `@/` maps to `src/` directory (configured in vite.config.ts and tsconfig.json)

### State Management Patterns

- **TanStack Query** for server state (though currently using mock data)
- **Local component state** for UI interactions
- **React Router** for navigation state
- No global state management library (Redux, Zustand, etc.) is used

### Form Handling

Forms use React Hook Form + Zod:
- Schema validation with Zod
- Form components from shadcn/ui
- Error handling and display
- Located in registration, login, and profile pages

## Key Features to Maintain

1. **Bilingual Support**: All user-facing text should have both English and Arabic versions
2. **Assessment Timer**: Must track elapsed time and support pause/resume
3. **Auto-save**: Answers should be auto-saved every 30 seconds during assessments
4. **Gamification**: XP, streaks, and achievement notifications
5. **Responsive Design**: Mobile-first approach using Tailwind breakpoints
6. **Code Editor**: Monaco Editor for technical assessments with syntax highlighting
7. **Accessibility**: Radix UI components are ARIA-compliant

## Lovable Integration

This project was initially generated using Lovable (lovable.dev):
- Project URL: https://lovable.dev/projects/86a922db-6a41-4063-895b-2cd8b916f439
- Changes made via Lovable are auto-committed to the repository
- `lovable-tagger` plugin is used in development mode for component tracking

## Important Constraints

- **No Backend**: Currently uses static data from `src/data/assessmentData.ts`
- **TypeScript**: Loose mode enabled (avoid strict type checking)
- **ESLint**: Unused variables/parameters are allowed (configured to warn/off)
- **Git**: This is not currently a git repository (no git hooks or pre-commit checks)