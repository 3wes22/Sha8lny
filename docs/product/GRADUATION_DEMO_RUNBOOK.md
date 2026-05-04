# Graduation Demo Runbook

This runbook keeps the evaluator story focused on the core product loop:

`assessment -> roadmap -> progress -> advisory`

## Demo Accounts

- New user: `demo.new@sha8alny.local` / `DemoPass123!`
- Returning user: `demo.progress@sha8alny.local` / `DemoPass123!`

The new user account is intentionally empty. The returning user is pre-seeded with:

- a completed backend assessment
- an active roadmap
- completed milestones and completed courses
- a current milestone in progress
- visible learning-hours and streak data

## Local Startup

### 1. Backend

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py seed_graduation_demo --reset
python3 manage.py runserver
```

Optional supporting data for the jobs page:

```bash
python3 manage.py seed_jobs --clear --count 24
```

### 2. Frontend

```bash
cd Frontend
npm install
npm run dev
```

The frontend points to `http://localhost:8000/api/v1` by default. Only set `VITE_API_BASE_URL` if the backend is running somewhere else.

## Hosted Demo Mode

The default runtime is hosted Gemini.

Use these settings in `Backend/.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

This is the recommended mode for the evaluator demo because it matches the current backend default path.

## Local AI Fallback

If hosted inference is unavailable, switch to Ollama:

```env
AI_PROVIDER=ollama
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e2b
```

The product should still stay usable if the AI runtime is unavailable:

- assessment and roadmap generation expose controlled failure states
- advisory shows a fallback assistant message instead of a broken blank surface

## Demo Script

### Path A: New User

1. Sign in as `demo.new@sha8alny.local`.
2. Open the assessment flow.
3. Complete the staged questions.
4. Show the generated assessment result.
5. Generate a roadmap and activate it.
6. Land on the dashboard and show the first next action.
7. Open advisory and ask what to focus on next.

### Path B: Returning User

1. Sign in as `demo.progress@sha8alny.local`.
2. Open the dashboard first.
3. Point out:
   - active roadmap
   - current phase
   - completed milestones
   - completed courses
   - streak and logged learning hours
   - next action
4. Open the roadmap view and show the active milestone.
5. Open advisory and ask for the next backend career move.
6. Open jobs as a supporting surface if needed.

## Reset Between Rehearsals

Use this command before each fresh demo pass:

```bash
cd Backend
source venv/bin/activate
python3 manage.py seed_graduation_demo --reset
```

If you also want the supporting jobs surface reset:

```bash
python3 manage.py seed_jobs --clear --count 24
```

## Verification

Recommended graduation-slice verification commands:

```bash
cd Backend
python3 manage.py check
pytest apps/assessments/tests/test_frontend_contracts.py apps/roadmaps/tests/test_frontend_contracts.py apps/advisory/tests.py apps/progress/tests.py apps/users/tests/test_demo_seed.py
```

```bash
cd Frontend
npm run test:run
```
