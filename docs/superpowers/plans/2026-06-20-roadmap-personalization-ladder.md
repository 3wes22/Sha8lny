# Roadmap Personalization Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a real 5-band beginner→job-ready learning ladder for all 8 roles and use the assessment to grey out the bands/milestones a learner has already mastered, with an assessment-derived label and a "revise" reopen path.

**Architecture:** A new authored ladder module (`ladder.py`) produces a 5-band blueprint per role; a pure `apply_assessment_baseline` (`baseline.py`) annotates each milestone with `completed`/`not_started` + a `from_assessment` flag based on level + ranked gap/mastery lists. Persistence writes those statuses and derives phase/roadmap rollups directly (no progress-engine recompute, so no completion notifications fire for pre-passed work). The serializer exposes the flag; the frontend relabels those rows and lets the learner reopen them via the existing progress endpoint.

**Tech Stack:** Django 4 / DRF, pytest, SQLite (dev); React + TypeScript + Vite, vitest.

## Global Constraints

- Python 3.10+; format with Black (max line length 100); imports via isort.
- All models inherit `apps.core.models.BaseModel`; reference users via `settings.AUTH_USER_MODEL`.
- Run `python manage.py makemigrations roadmaps` (app-scoped only — never bare `makemigrations`).
- No new third-party dependencies (backend or frontend).
- Backend gate: `pytest` stays green (currently 274 passing — must not regress).
- Frontend gates: `npm run test:run`, `npm run build`, `npm run lint` all pass.
- The 8 supported roles (`apps/assessments/role_graph.py:12`): `backend`, `frontend`, `data_science`, `fullstack`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`.
- Commit after each task. Backend commands run from `Backend/`; frontend from `Frontend/`.

---

## File Structure

**New files**
- `Backend/apps/roadmaps/ladder.py` — `ROLE_LADDERS` data + `build_ladder_blueprint(...)` (5-band structure for any role).
- `Backend/apps/roadmaps/baseline.py` — `apply_assessment_baseline(...)` pure function + `ENTRY_BAND_BY_LEVEL`.
- `Backend/apps/roadmaps/migrations/0002_milestone_completed_from_assessment.py` — generated.
- `Backend/apps/roadmaps/tests/test_ladder.py`, `Backend/apps/roadmaps/tests/test_baseline.py`.

**Modified files**
- `Backend/apps/roadmaps/models.py` — add `RoadmapMilestone.completed_from_assessment`.
- `Backend/apps/roadmaps/services.py` — `_build_personalized_phase_blueprint` delegates to ladder; `_create_personalized_structure` honors per-milestone status + sets phase rollups; `populate_ai_roadmap` applies baseline + sets roadmap completion.
- `Backend/apps/roadmaps/ai_pipeline.py` — structure-agnostic personalization prompt.
- `Backend/apps/roadmaps/serializers.py` — expose `completed_from_assessment` + computed `baseline_from_assessment`.
- `Backend/apps/progress/services.py` — clear the flag when a milestone leaves `completed`.
- `Frontend/src/lib/api.ts` — add fields to `RoadmapMilestone` / `RoadmapPhase`.
- `Frontend/src/features/roadmap/components/RoadmapMilestoneRow.tsx` — "Marked from your assessment · Revise".
- `Frontend/src/features/roadmap/components/RoadmapStation.tsx` — band caption when assessment-derived.

---

## Task 1: Add `completed_from_assessment` field + migration

**Files:**
- Modify: `Backend/apps/roadmaps/models.py:625` (insert before `completed_at`)
- Create: `Backend/apps/roadmaps/migrations/0002_milestone_completed_from_assessment.py` (generated)
- Test: `Backend/apps/roadmaps/tests/test_models.py` (create if absent)

**Interfaces:**
- Produces: `RoadmapMilestone.completed_from_assessment: bool` (default `False`).

- [ ] **Step 1: Write the failing test**

Create `Backend/apps/roadmaps/tests/test_models.py`:

```python
from decimal import Decimal

import pytest

from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
from apps.users.models import User


@pytest.mark.django_db
def test_milestone_completed_from_assessment_defaults_false():
    user = User.objects.create_user(
        auth0_id="m1", email="m1@example.com", username="m1",
        full_name="M1", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="beginner", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4,
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"),
    )
    assert milestone.completed_from_assessment is False

    milestone.completed_from_assessment = True
    milestone.save(update_fields=["completed_from_assessment", "updated_at"])
    milestone.refresh_from_db()
    assert milestone.completed_from_assessment is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/roadmaps/tests/test_models.py -v`
Expected: FAIL — `AttributeError`/`TypeError` (`completed_from_assessment` unknown).

- [ ] **Step 3: Add the field**

In `Backend/apps/roadmaps/models.py`, insert into `RoadmapMilestone` directly above the `completed_at` field (currently line 625):

```python
    completed_from_assessment = models.BooleanField(
        default=False,
        help_text="True when this milestone was marked complete from the user's "
                  "assessment baseline (already-mastered), not finished in-plan",
    )

```

- [ ] **Step 4: Generate and apply the migration**

Run: `python manage.py makemigrations roadmaps`
Expected: creates `0002_milestone_completed_from_assessment.py` adding one `BooleanField`.
Run: `python manage.py migrate roadmaps`
Expected: applies cleanly.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest apps/roadmaps/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/roadmaps/models.py apps/roadmaps/migrations/0002_milestone_completed_from_assessment.py apps/roadmaps/tests/test_models.py
git commit -m "feat(roadmaps): add completed_from_assessment flag to milestones"
```

---

## Task 2: `apply_assessment_baseline` pure function

**Files:**
- Create: `Backend/apps/roadmaps/baseline.py`
- Test: `Backend/apps/roadmaps/tests/test_baseline.py`

**Interfaces:**
- Produces:
  - `ENTRY_BAND_BY_LEVEL: dict[str, int]` = `{"beginner": 0, "intermediate": 1, "advanced": 2}`
  - `apply_assessment_baseline(phases: list[dict], current_level: str, gaps: list[str], mastered: list[str]) -> list[dict]` — returns a new list; each milestone dict gains `status` (`"completed"`/`"not_started"`) and `from_assessment` (`bool`). Input is the blueprint shape: `[{"milestones": [{"title": str, "skills": list[str], ...}], ...}, ...]`.
- Consumes (Task 5): called in `populate_ai_roadmap`.

- [ ] **Step 1: Write the failing tests**

Create `Backend/apps/roadmaps/tests/test_baseline.py`:

```python
from apps.roadmaps.baseline import apply_assessment_baseline


def _phases():
    # 5 bands, two milestones each, distinct skill keywords.
    return [
        {"title": "Foundations", "milestones": [
            {"title": "Learn HTTP basics", "skills": ["http"]},
            {"title": "Version control with Git", "skills": ["git"]},
        ]},
        {"title": "Core Skills", "milestones": [
            {"title": "Build a REST API", "skills": ["rest"]},
            {"title": "Relational databases and SQL", "skills": ["sql"]},
        ]},
        {"title": "Intermediate", "milestones": [
            {"title": "Automated testing", "skills": ["testing"]},
            {"title": "Caching fundamentals", "skills": ["caching"]},
        ]},
        {"title": "Advanced", "milestones": [
            {"title": "Containerization with Docker", "skills": ["docker"]},
            {"title": "Observability and tracing", "skills": ["observability"]},
        ]},
        {"title": "Job-Ready", "milestones": [
            {"title": "Ship a portfolio project", "skills": ["portfolio"]},
            {"title": "Targeted job search sprint", "skills": ["jobsearch"]},
        ]},
    ]


def _all(phase):
    return [(m["status"], m["from_assessment"]) for m in phase["milestones"]]


def test_beginner_passes_nothing():
    out = apply_assessment_baseline(_phases(), "beginner", gaps=[], mastered=[])
    for phase in out:
        for m in phase["milestones"]:
            assert m["status"] == "not_started"
            assert m["from_assessment"] is False


def test_intermediate_passes_foundations_only():
    out = apply_assessment_baseline(_phases(), "intermediate", gaps=[], mastered=[])
    assert all(s == ("completed", True) for s in _all(out[0]))   # Foundations
    assert all(s == ("not_started", False) for s in _all(out[1]))  # Core active


def test_advanced_passes_foundations_and_core():
    out = apply_assessment_baseline(_phases(), "advanced", gaps=[], mastered=[])
    assert all(s == ("completed", True) for s in _all(out[0]))
    assert all(s == ("completed", True) for s in _all(out[1]))
    assert all(s == ("not_started", False) for s in _all(out[2]))  # Intermediate active


def test_gap_in_passed_band_stays_active():
    # advanced learner but SQL is a flagged gap -> that Core milestone stays active.
    out = apply_assessment_baseline(_phases(), "advanced", gaps=["SQL"], mastered=[])
    core = {m["title"]: (m["status"], m["from_assessment"]) for m in out[1]["milestones"]}
    assert core["Relational databases and SQL"] == ("not_started", False)
    assert core["Build a REST API"] == ("completed", True)


def test_mastery_above_entry_prepasses_milestone():
    # beginner, but proven mastery of Docker -> that Advanced milestone is pre-passed.
    out = apply_assessment_baseline(_phases(), "beginner", gaps=[], mastered=["Docker"])
    adv = {m["title"]: (m["status"], m["from_assessment"]) for m in out[3]["milestones"]}
    assert adv["Containerization with Docker"] == ("completed", True)
    assert adv["Observability and tracing"] == ("not_started", False)


def test_does_not_mutate_input():
    phases = _phases()
    apply_assessment_baseline(phases, "advanced", gaps=[], mastered=[])
    assert "status" not in phases[0]["milestones"][0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/roadmaps/tests/test_baseline.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.roadmaps.baseline`.

- [ ] **Step 3: Implement `baseline.py`**

Create `Backend/apps/roadmaps/baseline.py`:

```python
"""Annotate a roadmap blueprint with assessment-derived completion.

Pure, side-effect-free. Bands below the learner's entry point are marked
already-passed (``completed`` + ``from_assessment=True``) unless a flagged gap
keeps an individual milestone active; bands at/above the entry point are active
unless a proven-mastery signal pre-passes a milestone. Gaps win ties.
"""

from __future__ import annotations

import copy
import re
from typing import Any

# How many leading bands a learner has already cleared, by proficiency level.
ENTRY_BAND_BY_LEVEL: dict[str, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}


def _tokens(label: str) -> list[str]:
    return [tok for tok in re.split(r"[^a-z0-9]+", label.lower()) if len(tok) >= 4]


def _matches(labels: list[str], text: str) -> bool:
    lowered = text.lower()
    for label in labels:
        for tok in _tokens(label):
            if tok in lowered:
                return True
    return False


def apply_assessment_baseline(
    phases: list[dict[str, Any]],
    current_level: str,
    gaps: list[str],
    mastered: list[str],
) -> list[dict[str, Any]]:
    """Return a deep copy of ``phases`` with per-milestone status + from_assessment."""
    entry = ENTRY_BAND_BY_LEVEL.get((current_level or "").lower(), 0)
    gaps = [g for g in (gaps or []) if g]
    mastered = [m for m in (mastered or []) if m]
    out = copy.deepcopy(phases)

    for band_idx, phase in enumerate(out):
        for milestone in phase.get("milestones", []):
            text = " ".join([
                str(milestone.get("title", "")),
                " ".join(str(s) for s in milestone.get("skills", [])),
            ])
            matches_gap = _matches(gaps, text)
            matches_mastery = _matches(mastered, text)

            if band_idx < entry and not matches_gap:
                milestone["status"] = "completed"
                milestone["from_assessment"] = True
            elif band_idx >= entry and matches_mastery and not matches_gap:
                milestone["status"] = "completed"
                milestone["from_assessment"] = True
            else:
                milestone["status"] = "not_started"
                milestone["from_assessment"] = False

    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest apps/roadmaps/tests/test_baseline.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/roadmaps/baseline.py apps/roadmaps/tests/test_baseline.py
git commit -m "feat(roadmaps): assessment-baseline annotation for blueprints"
```

---

## Task 3: `ROLE_LADDERS` + `build_ladder_blueprint`

**Files:**
- Create: `Backend/apps/roadmaps/ladder.py`
- Test: `Backend/apps/roadmaps/tests/test_ladder.py`

**Interfaces:**
- Consumes: `BASE_HOURS_BY_LEVEL`, `DEFAULT_BASE_HOURS`, `HOURS_PER_FOCUS_ITEM`, `MIN_PLAN_WEEKS`, `MIN_PHASE_WEEKS` from `apps.roadmaps.services`; `apps.roadmaps.services.RoadmapService._portfolio_project_title`; `apps.assessments.role_graph.resolve_role_key`.
- Produces: `build_ladder_blueprint(target_career: str, current_level: str, priority_skills: list[str], gaps: list[str], top_skills: list[str], strengths: list[str], weekly_hours: int) -> list[dict]` — 5 phase dicts shaped exactly like the existing blueprint: each `{"title", "description", "weeks", "objectives", "milestones": [{"title", "type", "hours", "skills"}]}`.

> Import note: to avoid a circular import (`services` will import `ladder` in Task 4), `build_ladder_blueprint` imports `RoadmapService` and the constants **inside the function body**, not at module top.

- [ ] **Step 1: Write the failing tests**

Create `Backend/apps/roadmaps/tests/test_ladder.py`:

```python
import pytest

from apps.assessments.role_graph import SUPPORTED_ROLES
from apps.roadmaps.ladder import ROLE_LADDERS, build_ladder_blueprint

CAREER_BY_ROLE = {
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "data_science": "Data Scientist",
    "fullstack": "Full Stack Developer",
    "devops": "DevOps Engineer",
    "android": "Android Developer",
    "machine_learning_engineer": "Machine Learning Engineer",
    "ui_ux_designer": "UI/UX Designer",
}


def test_all_supported_roles_have_authored_topics():
    for role in SUPPORTED_ROLES:
        assert role in ROLE_LADDERS, f"missing ladder for {role}"
        bands = ROLE_LADDERS[role]
        assert len(bands) == 4, f"{role} must author bands 0-3 (Job-Ready is generated)"
        for band in bands:
            assert len(band) >= 3, f"{role} band too thin: {band}"


@pytest.mark.parametrize("role", SUPPORTED_ROLES)
def test_build_blueprint_has_five_bands(role):
    phases = build_ladder_blueprint(
        target_career=CAREER_BY_ROLE[role],
        current_level="beginner",
        priority_skills=[],
        gaps=[],
        top_skills=[],
        strengths=[],
        weekly_hours=10,
    )
    assert len(phases) == 5
    for phase in phases:
        assert phase["title"]
        assert phase["weeks"] >= 1
        assert len(phase["milestones"]) >= 1
        for milestone in phase["milestones"]:
            assert milestone["title"]
            assert milestone["type"] in {"course", "project", "practice", "reading"}
            assert milestone["hours"] >= 1
    # Last band is the job-ready band and ends with a project + job-search work.
    job_band = phases[4]
    types = [m["type"] for m in job_band["milestones"]]
    assert "project" in types


def test_unknown_role_falls_back_to_generic_ladder():
    phases = build_ladder_blueprint(
        target_career="Quantum Basket Weaver",
        current_level="beginner",
        priority_skills=[], gaps=[], top_skills=[], strengths=[],
        weekly_hours=10,
    )
    assert len(phases) == 5
    assert all(len(p["milestones"]) >= 1 for p in phases)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/roadmaps/tests/test_ladder.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.roadmaps.ladder`.

- [ ] **Step 3: Implement `ladder.py`**

Create `Backend/apps/roadmaps/ladder.py`:

```python
"""Authored beginner→job-ready learning ladders per role.

Five fixed bands (Foundations → Core → Intermediate → Advanced → Job-Ready).
``ROLE_LADDERS`` authors bands 0-3 as topic-title lists per role (content drawn
from public references such as roadmap.sh paths and official docs, written
originally); the Job-Ready band is generated uniformly from role helpers.
"""

from __future__ import annotations

import math
from typing import Any

from apps.assessments.role_graph import resolve_role_key

BAND_TITLES = [
    "Foundations",
    "Core Skills",
    "Intermediate Skills",
    "Advanced Skills",
    "Job-Ready & Portfolio",
]

# Fraction of total plan weeks per band (sums to 1.0).
LADDER_WEEK_SPLIT = (0.18, 0.22, 0.24, 0.20, 0.16)

# Authored topic titles for bands 0-3 (Foundations, Core, Intermediate, Advanced).
ROLE_LADDERS: dict[str, list[list[str]]] = {
    "backend": [
        ["Programming fundamentals & a primary language", "Git & the command line",
         "How the web works (HTTP, DNS, client/server)", "Data structures & algorithms basics"],
        ["A web framework (Django/Express/Spring)", "HTTP & REST API design",
         "Relational databases & SQL", "Authentication basics (sessions, JWT)"],
        ["ORMs & data modeling", "Automated testing (unit & integration)",
         "Error handling & logging", "Caching fundamentals", "API versioning & pagination"],
        ["Scalability & load balancing", "Message queues & async workers",
         "Containerization (Docker)", "Observability (metrics & tracing)",
         "Security hardening (OWASP top 10)"],
    ],
    "frontend": [
        ["HTML semantics & forms", "CSS layout (flexbox & grid)",
         "JavaScript fundamentals & the DOM", "Git & package managers"],
        ["A UI framework (React/Vue/Angular)", "Component state & props",
         "Client-side routing", "Calling REST APIs & async data"],
        ["State management (Redux/Context/Pinia)", "Component & e2e testing",
         "Forms, validation & accessibility (a11y)", "Performance & bundling"],
        ["Server-side rendering & meta-frameworks (Next/Nuxt)", "TypeScript at scale",
         "Progressive Web Apps & caching", "Design systems & theming"],
    ],
    "data_science": [
        ["Python for data analysis", "Statistics & probability basics",
         "SQL & data querying", "Git & notebooks"],
        ["Pandas & data wrangling", "Exploratory data analysis & visualization",
         "Supervised ML fundamentals", "Model evaluation & validation"],
        ["Feature engineering", "Unsupervised learning & clustering",
         "Experiment design & A/B testing", "Storytelling & dashboards"],
        ["Time series & advanced models", "MLOps basics & reproducibility",
         "Big data tooling (Spark) basics", "Deploying models & APIs"],
    ],
    "fullstack": [
        ["Web fundamentals (HTTP, HTML/CSS, JS)", "A programming language & Git",
         "Relational data & SQL basics", "Command line & environments"],
        ["A frontend framework (React)", "A backend framework & REST APIs",
         "Database modeling & ORM", "Auth across the stack"],
        ["End-to-end testing", "API integration & error handling",
         "State management & caching", "File storage & third-party APIs"],
        ["Deployment & CI/CD", "Containerization (Docker)",
         "Performance & security hardening", "Realtime (websockets) basics"],
    ],
    "devops": [
        ["Linux fundamentals & shell scripting", "Networking (DNS, HTTP, TCP/IP)",
         "Git & version-control workflows", "A scripting language (Python/Bash)"],
        ["CI/CD pipelines", "Infrastructure as Code (Terraform)",
         "A cloud provider (AWS/GCP/Azure) basics", "Configuration management (Ansible)"],
        ["Containers (Docker)", "Container orchestration (Kubernetes)",
         "Monitoring & logging", "Secrets & config management"],
        ["Observability & tracing (SRE)", "Scaling & high availability",
         "Security & compliance (DevSecOps)", "Cost optimization & autoscaling"],
    ],
    "android": [
        ["Kotlin language fundamentals", "OOP & coroutines basics",
         "Git & Android Studio", "Android app & activity lifecycle"],
        ["Jetpack Compose UI", "App architecture (MVVM) & navigation",
         "Local persistence (Room)", "Networking (Retrofit) & REST"],
        ["Dependency injection (Hilt)", "Unit & UI testing",
         "Background work & WorkManager", "Material Design & theming"],
        ["Performance & memory profiling", "Modularization & build optimization",
         "CI for Android & signing", "Publishing to Google Play"],
    ],
    "machine_learning_engineer": [
        ["Python & software-engineering basics", "Linear algebra, calculus & probability",
         "ML fundamentals & scikit-learn", "Git & experiment tracking"],
        ["Deep learning frameworks (PyTorch/TensorFlow)", "Neural network architectures",
         "Data pipelines & preprocessing", "Model training & evaluation"],
        ["Model serving & APIs", "Feature stores & pipelines",
         "Experiment management & tuning", "Containerizing ML workloads"],
        ["Scaling training & distributed compute", "Model monitoring & drift",
         "MLOps & CI/CD for models", "Optimization & quantization"],
    ],
    "ui_ux_designer": [
        ["Design fundamentals (layout, color, typography)", "Visual hierarchy & composition",
         "Design tools (Figma) basics", "Design-to-dev handoff awareness"],
        ["User research & personas", "Wireframing & information architecture",
         "Prototyping & user flows", "Usability testing"],
        ["Design systems & components", "Interaction & motion design",
         "Accessibility (WCAG)", "Data-informed design"],
        ["Advanced prototyping & design ops", "Service & systems design",
         "Analytics & measuring UX", "Portfolio storytelling"],
    ],
}

GENERIC_LADDER_TEMPLATE = [
    ["Core fundamentals", "Tooling & version control", "Domain basics"],
    ["Primary {career} toolkit", "Applied practice", "Working with real data/APIs"],
    ["Testing & quality", "Intermediate patterns", "Integration & debugging"],
    ["Production concerns", "Performance & security", "Tooling & automation"],
]


def _generic_bands(career: str) -> list[list[str]]:
    return [[topic.format(career=career) for topic in band] for band in GENERIC_LADDER_TEMPLATE]


def _band_objectives(band_title: str, career: str) -> list[str]:
    return [
        f"Work through the {band_title.lower()} milestones for {career}.",
        f"Build durable confidence before advancing past {band_title}.",
    ]


def build_ladder_blueprint(
    *,
    target_career: str,
    current_level: str,
    priority_skills: list[str],
    gaps: list[str],
    top_skills: list[str],
    strengths: list[str],
    weekly_hours: int,
) -> list[dict[str, Any]]:
    """Build the 5-band ladder blueprint (status-agnostic; baseline runs later)."""
    # Local imports avoid a circular dependency with services.py.
    from apps.roadmaps.services import (
        BASE_HOURS_BY_LEVEL,
        DEFAULT_BASE_HOURS,
        HOURS_PER_FOCUS_ITEM,
        MIN_PHASE_WEEKS,
        MIN_PLAN_WEEKS,
        RoadmapService,
    )

    role_key = resolve_role_key(target_career)
    authored = ROLE_LADDERS.get(role_key) or _generic_bands(target_career)

    # Job-Ready band is generated uniformly from role helpers.
    job_band = [
        RoadmapService._portfolio_project_title(target_career),
        f"Interview & system-design prep for {target_career}",
        "Turn projects into resume & interview stories",
        f"Run a targeted {target_career} job-search sprint",
    ]
    band_topics = [*authored, job_band]

    focus_items = max(1, len(priority_skills) + len(gaps))
    base_hours = BASE_HOURS_BY_LEVEL.get(current_level, DEFAULT_BASE_HOURS)
    total_hours = base_hours + (focus_items * HOURS_PER_FOCUS_ITEM)
    total_weeks = max(MIN_PLAN_WEEKS, math.ceil(total_hours / max(weekly_hours, 1)))

    phases: list[dict[str, Any]] = []
    for band_idx, topics in enumerate(band_topics):
        weeks = max(MIN_PHASE_WEEKS, math.ceil(total_weeks * LADDER_WEEK_SPLIT[band_idx]))
        band_hours = max(len(topics) * 6, round(total_hours * LADDER_WEEK_SPLIT[band_idx]))
        hours_per = max(6, band_hours // max(len(topics), 1))
        is_job_band = band_idx == 4

        milestones: list[dict[str, Any]] = []
        for pos, title in enumerate(topics):
            if is_job_band:
                mtype = "project" if pos == 0 else "practice"
            else:
                mtype = "project" if (band_idx >= 1 and pos == len(topics) - 1) else "course"
            milestones.append({
                "title": title,
                "type": mtype,
                "hours": hours_per,
                "skills": [title],
            })

        band_title = BAND_TITLES[band_idx]
        phases.append({
            "title": f"{band_title}: {target_career}",
            "description": (
                f"{band_title} band of your {target_career} ladder — "
                f"comprehensive coverage from beginner to job-ready."
            ),
            "weeks": weeks,
            "objectives": _band_objectives(band_title, target_career),
            "milestones": milestones,
        })

    return phases
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest apps/roadmaps/tests/test_ladder.py -v`
Expected: PASS (all 8 roles parametrized + generic fallback).

- [ ] **Step 5: Commit**

```bash
git add apps/roadmaps/ladder.py apps/roadmaps/tests/test_ladder.py
git commit -m "feat(roadmaps): authored 5-band ladders for all 8 roles"
```

---

## Task 4: Wire the ladder into generation + structure-agnostic AI prompt

**Files:**
- Modify: `Backend/apps/roadmaps/services.py:602-694` (`_build_personalized_phase_blueprint` body)
- Modify: `Backend/apps/roadmaps/ai_pipeline.py:16-18` (prompt)
- Test: `Backend/apps/roadmaps/tests/test_api.py` (add one test)

**Interfaces:**
- Consumes: `build_ladder_blueprint` (Task 3).
- Produces: `_build_personalized_phase_blueprint(...)` now returns the 5-band ladder (same call signature, so `assembler.py:210` is unchanged).

- [ ] **Step 1: Add a shared `loop_user` fixture to `test_api.py`**

The `loop_user` fixture lives in `test_full_loop.py` and is **not** visible to `test_api.py` (no shared conftest). Add it near the top of `Backend/apps/roadmaps/tests/test_api.py` (skip if it already exists there):

```python
@pytest.fixture
def loop_user(db):
    from apps.users.models import User

    return User.objects.create_user(
        auth0_id="ladder_auth0", email="ladder@example.com", username="ladder_user",
        full_name="Ladder User", date_of_birth="1997-01-01",
    )
```

- [ ] **Step 2: Write the failing test**

Append to `Backend/apps/roadmaps/tests/test_api.py`. The `generate_structured` patch forces the deterministic fallback so the test never touches the network:

```python
@pytest.mark.django_db
def test_generation_produces_five_band_ladder(loop_user):
    from unittest.mock import patch

    from apps.assessments.models import Assessment, AssessmentResult
    from apps.roadmaps.models import Roadmap
    from apps.roadmaps.services import RoadmapService

    assessment = Assessment.objects.create(
        user=loop_user, assessment_type="skills", target_career="Backend Developer",
        questions=[], total_questions=0, status="completed", ai_processing_status="completed",
    )
    AssessmentResult.objects.create(
        assessment=assessment, overall_score=40, skill_scores={"python": 40},
        strengths=["Python"], areas_for_improvement=["System design"],
        recommended_careers=[{"title": "Backend Developer", "match_score": 80}],
        recommended_learning_paths=[], ai_insights="x", llm_model_used="mock", ai_confidence_score=0.7,
    )
    roadmap = Roadmap.objects.create(
        user=loop_user, title="R", target_career="Backend Developer", assessment=assessment,
        current_level="beginner", target_level="job-ready", estimated_duration_weeks=12,
        weekly_hours_commitment=10, status=Roadmap.DRAFT, ai_processing_status="pending",
    )
    with patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks", return_value=[]), \
         patch("apps.roadmaps.ai_pipeline.GemmaClient.generate_structured", side_effect=RuntimeError("offline")):
        RoadmapService.populate_ai_roadmap(roadmap)

    phases = list(roadmap.phases.order_by("order"))
    assert len(phases) == 5
    assert "Foundations" in phases[0].title
    assert "Job-Ready" in phases[4].title
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest apps/roadmaps/tests/test_api.py::test_generation_produces_five_band_ladder -v`
Expected: FAIL — 3 phases, not 5 (`assert 3 == 5`).

- [ ] **Step 4: Replace `_build_personalized_phase_blueprint` body**

In `Backend/apps/roadmaps/services.py`, replace the entire body of `_build_personalized_phase_blueprint` (the docstring + all logic from line 611 down to the closing `]` at line 694) with a delegation:

```python
        """Create the assessment-aware 5-band ladder blueprint."""
        from apps.roadmaps.ladder import build_ladder_blueprint

        return build_ladder_blueprint(
            target_career=target_career,
            current_level=current_level,
            priority_skills=priority_skills,
            gaps=gaps,
            top_skills=top_skills,
            strengths=strengths,
            weekly_hours=weekly_hours,
        )
```

Keep the method signature line (`def _build_personalized_phase_blueprint(...)` with its existing parameters) unchanged.

- [ ] **Step 5: Make the AI prompt structure-agnostic**

In `Backend/apps/roadmaps/ai_pipeline.py`, replace `ROADMAP_PERSONALIZATION_PROMPT` (lines 16-18):

```python
ROADMAP_PERSONALIZATION_PROMPT = """You rewrite a fixed multi-phase learning roadmap blueprint into motivating, personalized copy for a {career} learner currently at {current_level} aiming for {target_level}, with ~{weekly_hours} hrs/week.
Prioritize their gaps: {gaps}. Build on strengths: {strengths}.
Return STRICT JSON preserving the given phase/milestone structure and ids exactly; do NOT add, remove, or reorder phases or milestones; only improve title, description, and next_action text. Keep each description under 240 characters."""
```

- [ ] **Step 6: Run the test + the blueprint/ladder suites**

Run: `pytest apps/roadmaps/tests/test_api.py::test_generation_produces_five_band_ladder apps/roadmaps/tests/test_ladder.py apps/roadmaps/tests/test_assembler.py -v`
Expected: PASS. (If `test_assembler.py` asserted the old 3-phase titles, update those assertions to the new band titles in the same commit.)

- [ ] **Step 7: Commit**

```bash
git add apps/roadmaps/services.py apps/roadmaps/ai_pipeline.py apps/roadmaps/tests/test_api.py apps/roadmaps/tests/test_assembler.py
git commit -m "feat(roadmaps): generate 5-band ladder; structure-agnostic AI prompt"
```

---

## Task 5: Apply baseline + write rollups during generation

**Files:**
- Modify: `Backend/apps/roadmaps/services.py:696-725` (`_create_personalized_structure`)
- Modify: `Backend/apps/roadmaps/services.py:899-913` (`populate_ai_roadmap`: apply baseline before persist) and the final `roadmap.save(...)` (add completion)
- Test: `Backend/apps/roadmaps/tests/test_api.py` (add tests)

**Interfaces:**
- Consumes: `apply_assessment_baseline` (Task 2); `completed_from_assessment` field (Task 1).
- Produces: persisted milestones honor `status`/`from_assessment`; phases get derived `status`/`completion_percentage`; `roadmap.completion_percentage` reflects pre-passed work.

> **Line numbers are from the original `services.py` and will have shifted** because Task 4 shrank `_build_personalized_phase_blueprint` by ~80 lines. Locate each edit by the **quoted code**, not the line number.

- [ ] **Step 1: Write the failing tests**

Append to `Backend/apps/roadmaps/tests/test_api.py`:

```python
def _make_advanced_backend_roadmap(user):
    from apps.assessments.models import Assessment, AssessmentResult
    from apps.roadmaps.models import Roadmap

    assessment = Assessment.objects.create(
        user=user, assessment_type="skills", target_career="Backend Developer",
        questions=[], total_questions=0, status="completed", ai_processing_status="completed",
    )
    AssessmentResult.objects.create(
        assessment=assessment, overall_score=88, skill_scores={"python": 90},
        strengths=["Python"], areas_for_improvement=["Observability"],
        recommended_careers=[{"title": "Backend Developer", "match_score": 92}],
        recommended_learning_paths=[], ai_insights="x", llm_model_used="mock", ai_confidence_score=0.9,
    )
    return Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer", assessment=assessment,
        current_level="advanced", target_level="job-ready", estimated_duration_weeks=12,
        weekly_hours_commitment=10, status=Roadmap.DRAFT, ai_processing_status="pending",
    )


@pytest.mark.django_db
def test_advanced_learner_greys_first_two_bands(loop_user):
    from unittest.mock import patch
    from apps.roadmaps.services import RoadmapService

    roadmap = _make_advanced_backend_roadmap(loop_user)
    with patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks", return_value=[]), \
         patch("apps.roadmaps.ai_pipeline.GemmaClient.generate_structured", side_effect=RuntimeError("offline")):
        RoadmapService.populate_ai_roadmap(roadmap)

    phases = list(roadmap.phases.order_by("order"))
    # Foundations + Core fully passed from assessment.
    for phase in phases[:2]:
        assert phase.status == "completed"
        assert all(m.status == "completed" and m.completed_from_assessment
                   for m in phase.milestones.all())
    # Intermediate band onward is active (not from assessment).
    assert phases[2].status in {"not_started", "in_progress"}
    assert any(not m.completed_from_assessment for m in phases[2].milestones.all())
    # Headline completion reflects the assessment baseline.
    assert float(roadmap.completion_percentage) > 0


@pytest.mark.django_db
def test_baseline_persist_fires_no_completion_notifications(loop_user):
    from unittest.mock import patch
    from apps.roadmaps.services import RoadmapService

    roadmap = _make_advanced_backend_roadmap(loop_user)
    with patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks", return_value=[]), \
         patch("apps.roadmaps.ai_pipeline.GemmaClient.generate_structured", side_effect=RuntimeError("offline")), \
         patch("apps.progress.services.ProgressService.update_progress_metrics") as recompute:
        RoadmapService.populate_ai_roadmap(roadmap)
    # Generation must NOT route baseline through the progress recompute.
    recompute.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/roadmaps/tests/test_api.py::test_advanced_learner_greys_first_two_bands -v`
Expected: FAIL — phases are `not_started` (baseline not wired yet).

- [ ] **Step 3: Update `_create_personalized_structure` to honor status + roll up phases**

In `Backend/apps/roadmaps/services.py`, replace `_create_personalized_structure` (lines 696-725) with:

```python
    @staticmethod
    def _create_personalized_structure(roadmap: Roadmap, phases_data: List[Dict[str, Any]]) -> None:
        """Persist the generated roadmap hierarchy with assessment-derived statuses."""
        now = timezone.now()
        for phase_idx, phase_data in enumerate(phases_data, start=1):
            phase = RoadmapPhase.objects.create(
                roadmap=roadmap,
                title=phase_data['title'],
                description=phase_data['description'],
                order=phase_idx,
                estimated_duration_weeks=phase_data['weeks'],
                status='not_started',
                objectives=phase_data.get('objectives', []),
            )

            milestones = phase_data.get('milestones', [])
            for milestone_idx, milestone_data in enumerate(milestones, start=1):
                m_status = milestone_data.get('status', 'not_started')
                from_assessment = bool(milestone_data.get('from_assessment', False))
                RoadmapMilestone.objects.create(
                    phase=phase,
                    title=milestone_data['title'],
                    description=(
                        milestone_data.get('description')
                        or f"Complete {milestone_data['title']} during the {phase.title} phase."
                    ),
                    milestone_type=milestone_data['type'],
                    order=milestone_idx,
                    estimated_duration_hours=Decimal(str(milestone_data['hours'])),
                    status=m_status,
                    completed_from_assessment=from_assessment,
                    completed_at=now if m_status == 'completed' else None,
                    is_required=True,
                    skills=milestone_data.get('skills', []),
                    resources=milestone_data.get('resources', []),
                )

            # Derive phase status/completion from its milestones (no signals fired).
            total = len(milestones)
            completed = sum(1 for m in milestones if m.get('status') == 'completed')
            if total and completed == total:
                phase.status = 'completed'
                phase.completion_percentage = Decimal('100.00')
                phase.completed_at = now
                phase.started_at = now
            elif completed:
                phase.status = 'in_progress'
                phase.completion_percentage = Decimal(str(round(completed / total * 100, 2)))
                phase.started_at = now
            else:
                phase.status = 'not_started'
                phase.completion_percentage = Decimal('0.00')
            phase.save(update_fields=[
                'status', 'completion_percentage', 'started_at', 'completed_at', 'updated_at',
            ])
```

- [ ] **Step 4: Apply baseline before persist + set roadmap completion in `populate_ai_roadmap`**

In `Backend/apps/roadmaps/services.py`, in `populate_ai_roadmap`, replace lines 912-913:

```python
        roadmap.phases.all().delete()
        RoadmapService._create_personalized_structure(roadmap, personalization.phases)
```

with:

```python
        from apps.roadmaps.baseline import apply_assessment_baseline

        mastered = RoadmapService._dedupe_preserve_order([*top_skills, *strengths])
        baselined_phases = apply_assessment_baseline(
            personalization.phases, roadmap.current_level, gaps, mastered,
        )
        roadmap.phases.all().delete()
        RoadmapService._create_personalized_structure(roadmap, baselined_phases)
```

Then set the roadmap-level completion. Just before the final `roadmap.save(update_fields=[...])` (line 944), add:

```python
        roadmap.completion_percentage = RoadmapService._baseline_completion_percentage(roadmap)
```

and add `'completion_percentage'` to that `update_fields` list.

- [ ] **Step 5: Add the `_baseline_completion_percentage` helper**

In `Backend/apps/roadmaps/services.py`, add this static method to `RoadmapService` (next to `_create_personalized_structure`):

```python
    @staticmethod
    def _baseline_completion_percentage(roadmap: Roadmap) -> Decimal:
        """Roadmap completion from persisted milestone statuses (no side effects)."""
        milestones = RoadmapMilestone.objects.filter(phase__roadmap=roadmap)
        total = milestones.count()
        if not total:
            return Decimal('0.00')
        completed = milestones.filter(status=RoadmapMilestone.COMPLETED).count()
        return Decimal(str(round(completed / total * 100, 2)))
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest apps/roadmaps/tests/test_api.py::test_advanced_learner_greys_first_two_bands apps/roadmaps/tests/test_api.py::test_baseline_persist_fires_no_completion_notifications -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/roadmaps/services.py apps/roadmaps/tests/test_api.py
git commit -m "feat(roadmaps): apply assessment baseline + rollups at generation"
```

---

## Task 6: Expose the flag + computed `baseline_from_assessment` in serializers

**Files:**
- Modify: `Backend/apps/roadmaps/serializers.py:102-160` (milestone serializers) and `186-229` (phase serializer)
- Test: `Backend/apps/roadmaps/tests/test_frontend_contracts.py`

**Interfaces:**
- Produces: milestone JSON includes `completed_from_assessment: bool`; phase JSON includes `baseline_from_assessment: bool` (= phase has ≥1 milestone and every `completed`/`skipped` milestone is from-assessment).

- [ ] **Step 1: Write the failing test**

Append to `Backend/apps/roadmaps/tests/test_frontend_contracts.py`:

```python
@pytest.mark.django_db
def test_serializer_exposes_assessment_baseline_fields():
    from decimal import Decimal
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapPhaseSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc1", email="sc1@example.com", username="sc1",
        full_name="SC1", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="completed",
    )
    RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=True,
    )

    data = RoadmapPhaseSerializer(phase).data
    assert data["milestones"][0]["completed_from_assessment"] is True
    assert data["baseline_from_assessment"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/roadmaps/tests/test_frontend_contracts.py::test_serializer_exposes_assessment_baseline_fields -v`
Expected: FAIL — `KeyError: 'completed_from_assessment'`.

- [ ] **Step 3: Add the field to both milestone serializers**

In `Backend/apps/roadmaps/serializers.py`, add `'completed_from_assessment'` to the `fields` list of `RoadmapMilestoneListSerializer` (after `'status'`, line 112) and `RoadmapMilestoneSerializer` (after `'status'`, line 135).

- [ ] **Step 4: Add the computed phase field**

In `RoadmapPhaseSerializer`, add a method field. After line 193 (`next_action = serializers.SerializerMethodField()`) add:

```python
    baseline_from_assessment = serializers.SerializerMethodField()
```

Add `'baseline_from_assessment'` to its `fields` list (after `'total_milestones'`, line 210). Then add the method (next to `get_next_action`):

```python
    def get_baseline_from_assessment(self, obj):
        milestones = list(obj.milestones.all())
        finished = [m for m in milestones
                    if m.status in (RoadmapMilestone.COMPLETED, RoadmapMilestone.SKIPPED)]
        return bool(finished) and all(m.completed_from_assessment for m in finished)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest apps/roadmaps/tests/test_frontend_contracts.py::test_serializer_exposes_assessment_baseline_fields -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/roadmaps/serializers.py apps/roadmaps/tests/test_frontend_contracts.py
git commit -m "feat(roadmaps): expose assessment-baseline fields in serializers"
```

---

## Task 7: Clear the flag when a milestone is reopened (revise)

**Files:**
- Modify: `Backend/apps/progress/services.py:542-545` (`MilestoneService.update_milestone_status`)
- Test: `Backend/apps/roadmaps/tests/test_api.py`

**Interfaces:**
- Consumes: `completed_from_assessment` field (Task 1).
- Produces: moving a milestone out of `completed` (e.g. to `not_started`) clears `completed_from_assessment`.

- [ ] **Step 1: Write the failing test**

Append to `Backend/apps/roadmaps/tests/test_api.py`:

```python
@pytest.mark.django_db
def test_reopening_assessment_milestone_clears_flag(loop_user):
    from decimal import Decimal
    from apps.progress.services import MilestoneService
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase

    roadmap = Roadmap.objects.create(
        user=loop_user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="completed",
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=True,
    )

    MilestoneService.update_milestone_status(loop_user, milestone, "not_started")
    milestone.refresh_from_db()
    assert milestone.status == "not_started"
    assert milestone.completed_from_assessment is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/roadmaps/tests/test_api.py::test_reopening_assessment_milestone_clears_flag -v`
Expected: FAIL — `completed_from_assessment` still `True`.

- [ ] **Step 3: Clear the flag in the non-completed branch**

In `Backend/apps/progress/services.py`, replace lines 542-545:

```python
        milestone.status = status
        if status == RoadmapMilestone.NOT_STARTED:
            milestone.completed_at = None
        milestone.save(update_fields=["status", "completed_at", "updated_at"])
```

with:

```python
        milestone.status = status
        if status == RoadmapMilestone.NOT_STARTED:
            milestone.completed_at = None
        # Leaving "completed" means the learner is redoing it: drop the
        # assessment-baseline marker so it reads as real in-plan work.
        milestone.completed_from_assessment = False
        milestone.save(update_fields=[
            "status", "completed_at", "completed_from_assessment", "updated_at",
        ])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/roadmaps/tests/test_api.py::test_reopening_assessment_milestone_clears_flag -v`
Expected: PASS.

- [ ] **Step 5: Run the full backend suite (no regressions)**

Run: `pytest`
Expected: all pass (≥ 274 + the new tests).

- [ ] **Step 6: Commit**

```bash
git add apps/progress/services.py apps/roadmaps/tests/test_api.py
git commit -m "feat(progress): clear assessment-baseline flag when reopening a milestone"
```

---

## Task 8: Frontend — API types + "Marked from your assessment · Revise" row

**Files:**
- Modify: `Frontend/src/lib/api.ts:357-394` (`RoadmapMilestone`, `RoadmapPhase` types)
- Modify: `Frontend/src/features/roadmap/components/RoadmapMilestoneRow.tsx`
- Test: `Frontend/src/features/roadmap/components/RoadmapMilestoneRow.test.tsx`

**Interfaces:**
- Consumes: serializer fields (Task 6).
- Produces: a milestone with `completed_from_assessment` shows a "Marked from your assessment" label + a "Revise" affordance; clicking still calls `onToggle(milestone)` (which the page maps to `not_started`).

- [ ] **Step 1: Add the API type fields**

In `Frontend/src/lib/api.ts`, add to `RoadmapMilestone` (after `completed_at?: string;`, line 368):

```typescript
  completed_from_assessment?: boolean;
```

And to `RoadmapPhase` (after `total_milestones?: number;`, line 390):

```typescript
  baseline_from_assessment?: boolean;
```

- [ ] **Step 2: Write the failing test**

`RoadmapMilestoneRow.test.tsx` already exists. **Append** the new `describe` block below to the end of it — do not delete the existing tests. Ensure these symbols are imported at the top of the file (add only the ones not already imported): `fireEvent`, `render`, `screen` from `@testing-library/react`; `describe`, `expect`, `it`, `vi` from `vitest`; `RoadmapMilestoneRow` from `@/features/roadmap/components/RoadmapMilestoneRow`; and the `RoadmapMilestone` type from `@/lib/api`. Then append:

```tsx
const baseMilestone: RoadmapMilestone = {
  id: "m1",
  title: "Learn HTTP basics",
  description: "",
  milestone_type: "course",
  order: 1,
  estimated_duration_hours: "10.00",
  status: "completed",
  is_required: true,
  skills: [],
  resources: [],
  completed_from_assessment: true,
};

describe("RoadmapMilestoneRow assessment baseline", () => {
  it("labels assessment-derived completions and offers Revise", () => {
    render(<RoadmapMilestoneRow milestone={baseMilestone} onToggle={() => {}} />);
    expect(screen.getByText(/from your assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/revise/i)).toBeInTheDocument();
  });

  it("calls onToggle when an assessment row is clicked (to reopen)", () => {
    const onToggle = vi.fn();
    render(<RoadmapMilestoneRow milestone={baseMilestone} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith(baseMilestone);
  });
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `npm run test:run -- RoadmapMilestoneRow`
Expected: FAIL — no "from your assessment" / "Revise" text.

- [ ] **Step 4: Implement the relabel**

In `Frontend/src/features/roadmap/components/RoadmapMilestoneRow.tsx`, replace the body of the component (from `const isComplete = ...` through the closing `</button>`) with:

```tsx
  const isComplete = milestone.status === "completed";
  const fromAssessment = isComplete && milestone.completed_from_assessment === true;

  return (
    <button
      aria-checked={isComplete}
      className={cn(
        "transition-smooth group flex w-full items-center gap-3 rounded-xl border border-border/60 bg-background/60 px-3 py-2.5 text-left",
        disabled ? "cursor-not-allowed opacity-60" : "hover:border-primary/40 hover:text-foreground",
      )}
      disabled={disabled}
      onClick={() => onToggle(milestone)}
      role="checkbox"
      type="button"
    >
      <span
        aria-hidden="true"
        className={cn(
          "transition-smooth flex h-5 w-5 flex-none items-center justify-center rounded-md border-2",
          isComplete ? "border-success bg-success text-success-foreground" : "border-border group-hover:border-primary",
        )}
      >
        {isComplete ? <Check className="h-3 w-3" /> : null}
      </span>

      <span className="flex min-w-0 flex-1 flex-col">
        <span className={cn("min-w-0 text-sm", isComplete && "text-muted-foreground line-through")}>
          {milestone.title}
        </span>
        {fromAssessment ? (
          <span className="text-[0.7rem] font-medium text-muted-foreground no-underline">
            Marked from your assessment ·{" "}
            <span className="text-primary underline-offset-2 group-hover:underline">Revise</span>
          </span>
        ) : null}
      </span>

      <span
        className={cn(
          "hidden flex-none rounded-full border px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide sm:inline-block",
          typePillClass[milestone.milestone_type] ?? "bg-muted/50 text-muted-foreground border-border/60",
        )}
      >
        {milestone.milestone_type}
      </span>

      <span className="flex flex-none items-center gap-1 text-xs text-muted-foreground">
        <Clock3 className="h-3.5 w-3.5" />
        {milestone.estimated_duration_hours}h
      </span>
    </button>
  );
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `npm run test:run -- RoadmapMilestoneRow`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/lib/api.ts src/features/roadmap/components/RoadmapMilestoneRow.tsx src/features/roadmap/components/RoadmapMilestoneRow.test.tsx
git commit -m "feat(roadmap-ui): label assessment-derived milestones with Revise affordance"
```

---

## Task 9: Frontend — band caption when assessment-derived

**Files:**
- Modify: `Frontend/src/features/roadmap/components/RoadmapStation.tsx`
- Test: `Frontend/src/features/roadmap/components/RoadmapStation.test.tsx`

**Interfaces:**
- Consumes: `RoadmapPhase.baseline_from_assessment` (Task 8 type), `StationState`.
- Produces: a completed, assessment-derived station renders a "Set from your assessment — expand to revise" caption.

- [ ] **Step 1: Write the failing test**

Add to `Frontend/src/features/roadmap/components/RoadmapStation.test.tsx` (read the file first to reuse its existing phase factory/imports; add this case):

```tsx
it("shows an assessment-baseline caption on a passed station", () => {
  const phase = {
    id: "p1",
    title: "Foundations: Backend Developer",
    description: "",
    order: 1,
    estimated_duration_weeks: 4,
    status: "completed" as const,
    completion_percentage: "100.00",
    objectives: [],
    milestones: [],
    baseline_from_assessment: true,
  };
  render(
    <RoadmapStation
      phase={phase}
      index={0}
      state="completed"
      expanded={false}
      onToggleExpand={() => {}}
      onMilestoneToggle={() => {}}
    />,
  );
  expect(screen.getByText(/set from your assessment/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:run -- RoadmapStation`
Expected: FAIL — caption not found.

- [ ] **Step 3: Render the caption**

In `Frontend/src/features/roadmap/components/RoadmapStation.tsx`, inside the header `<button>`, replace the current-state paragraph block (lines 102-106) with:

```tsx
            {state === "current" ? (
              <p className="mt-1 text-sm text-muted-foreground">
                {completion.toFixed(0)}% complete · {phase.estimated_duration_weeks} weeks
              </p>
            ) : null}
            {state === "completed" && phase.baseline_from_assessment ? (
              <p className="mt-1 text-sm text-muted-foreground">
                Set from your assessment — expand to revise
              </p>
            ) : null}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test:run -- RoadmapStation`
Expected: PASS.

- [ ] **Step 5: Frontend gates**

Run: `npm run test:run && npm run build && npm run lint`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/features/roadmap/components/RoadmapStation.tsx src/features/roadmap/components/RoadmapStation.test.tsx
git commit -m "feat(roadmap-ui): caption assessment-derived passed stations"
```

---

## Final verification

- [ ] **Backend:** from `Backend/`, run `pytest` — all pass, no regression.
- [ ] **Frontend:** from `Frontend/`, run `npm run test:run && npm run build && npm run lint` — all pass.
- [ ] **Manual smoke (optional):** generate a roadmap for an advanced learner and confirm the first two bands render greyed/collapsed with the "Set from your assessment" caption, while the remaining bands form the active plan.
