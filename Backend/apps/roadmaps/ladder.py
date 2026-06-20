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
