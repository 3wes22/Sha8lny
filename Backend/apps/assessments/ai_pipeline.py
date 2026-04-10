"""
Assessment-specific AI prompts, career question banks, and deterministic fallbacks.

Each career path has a dedicated question bank covering 6 dimensions:
  1. Core Technical — primary skill depth for the role
  2. Tooling/Ecosystem — knowledge of daily tools and frameworks
  3. Problem Solving — debugging and reasoning approach
  4. Experience — career stage and project complexity
  5. Goals — motivation and target outcome
  6. Commitment — available time and learning pace
"""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from apps.assessments.models import Assessment
from apps.assessments.services import BaselineAssessmentAnalyzer
from apps.core.ai_contracts import AssessmentAnalysisInput, AssessmentAnalysisResult
from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaClient, GemmaResponse


# ============================================================================
# DIMENSION WEIGHTS — used by both baseline scorer and LLM rubric
# ============================================================================

DIMENSION_WEIGHTS: Dict[str, float] = {
    "technical_depth": 0.25,
    "tooling": 0.15,
    "problem_solving": 0.20,
    "experience": 0.20,
    "goals": 0.10,
    "commitment": 0.10,
}


# ============================================================================
# CAREER-SPECIFIC QUESTION BANKS
# ============================================================================

_BACKEND_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you designing and building REST APIs?",
        "category": "API Design",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't built an API before", "score": 1},
            {"value": "basic", "label": "I've followed tutorials to build one", "score": 2},
            {"value": "mid", "label": "I can build CRUD APIs independently", "score": 4},
            {"value": "adv", "label": "I design APIs with auth, pagination, and versioning", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which databases and ORMs have you worked with?",
        "category": "Databases & ORMs",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't used a database yet", "score": 1},
            {"value": "basic", "label": "Basic SQL queries (SELECT, INSERT)", "score": 2},
            {"value": "mid", "label": "Comfortable with JOINs, indexes, and an ORM like Django ORM", "score": 4},
            {"value": "adv", "label": "Query optimization, migrations, replication, or multiple DB engines", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When you hit a server error you've never seen, how confident are you in diagnosing it?",
        "category": "Debugging",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I'd be stuck without help", "5": "I systematically read logs, trace the stack, and isolate the issue"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex backend project you've worked on?",
        "category": "Project Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't built a backend project yet", "score": 1},
            {"value": "tutorial", "label": "Tutorial-level apps (todo list, blog)", "score": 2},
            {"value": "personal", "label": "A multi-model app with auth that I designed myself", "score": 4},
            {"value": "production", "label": "Production or team-based systems with deployment", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal as a backend developer in the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: land my first backend job, switch from frontend, go freelance, get promoted to senior, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning backend development?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


_FRONTEND_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you building responsive user interfaces from a design mockup?",
        "category": "UI Implementation",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't built a UI from a design before", "score": 1},
            {"value": "basic", "label": "I can match simple layouts with HTML & CSS", "score": 2},
            {"value": "mid", "label": "I can build responsive, pixel-accurate pages independently", "score": 4},
            {"value": "adv", "label": "I implement complex layouts with animations, accessibility, and cross-browser support", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which frontend frameworks or libraries have you used in a real project?",
        "category": "Frameworks",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "None yet — just vanilla HTML/CSS/JS", "score": 1},
            {"value": "basic", "label": "Followed a React or Vue tutorial to completion", "score": 2},
            {"value": "mid", "label": "Built a multi-page app with React (or Vue/Angular) and state management", "score": 4},
            {"value": "adv", "label": "Used TypeScript, React Query, testing libraries, and component design systems", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When a component renders incorrectly or an API call fails silently, how confident are you in finding the cause?",
        "category": "Debugging",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I'd be stuck without help", "5": "I use DevTools, React profiler, and network tab instinctively"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex frontend project you've built?",
        "category": "Project Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't built a frontend project yet", "score": 1},
            {"value": "tutorial", "label": "Simple pages or tutorial clones", "score": 2},
            {"value": "personal", "label": "A multi-page app with routing, API calls, and auth", "score": 4},
            {"value": "production", "label": "Production apps with testing, CI/CD, and team collaboration", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal as a frontend developer in the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: land a React developer job, improve my styling skills, learn TypeScript, freelance, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning frontend development?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


_DATA_SCIENCE_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you with data analysis using Python (Pandas, NumPy)?",
        "category": "Data Analysis",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't done data analysis in Python", "score": 1},
            {"value": "basic", "label": "I can load CSVs and do basic filtering / grouping", "score": 2},
            {"value": "mid", "label": "I do EDA, handle missing data, and create visualizations independently", "score": 4},
            {"value": "adv", "label": "I build pipelines with feature engineering, statistical tests, and ML models", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which data tools and platforms have you used?",
        "category": "Data Tools",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "Just spreadsheets (Excel / Google Sheets)", "score": 1},
            {"value": "basic", "label": "Jupyter notebooks and basic Matplotlib/Seaborn", "score": 2},
            {"value": "mid", "label": "SQL databases, Scikit-learn, and a cloud platform (Kaggle, Colab)", "score": 4},
            {"value": "adv", "label": "TensorFlow/PyTorch, MLflow, Airflow, or similar production tools", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When your model's accuracy drops unexpectedly, how confident are you in diagnosing why?",
        "category": "Analytical Reasoning",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I wouldn't know where to start", "5": "I check data drift, feature importance, overfitting, and retrain systematically"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex data project you've completed?",
        "category": "Project Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't done a data project yet", "score": 1},
            {"value": "tutorial", "label": "Followed a Kaggle tutorial or course project", "score": 2},
            {"value": "personal", "label": "Built my own analysis / prediction project with real data", "score": 4},
            {"value": "production", "label": "Deployed a model or delivered insights used by stakeholders", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal in data science over the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: become a data analyst, learn machine learning, get a Kaggle medal, transition from software engineering, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning data science?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


_FULLSTACK_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you building an end-to-end feature — from database schema through API to UI?",
        "category": "Full-Stack Execution",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I've only worked on one side (frontend or backend)", "score": 1},
            {"value": "basic", "label": "I've connected a frontend to an API in a tutorial", "score": 2},
            {"value": "mid", "label": "I can build and ship a complete feature across front and back", "score": 4},
            {"value": "adv", "label": "I own full features including auth, deployment, and testing", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which technology stacks have you used for a complete project?",
        "category": "Stack Knowledge",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't built a full-stack project yet", "score": 1},
            {"value": "basic", "label": "Basic HTML/CSS + a simple backend (Flask, Express)", "score": 2},
            {"value": "mid", "label": "React + Django/Node + PostgreSQL or similar", "score": 4},
            {"value": "adv", "label": "Full stack with TypeScript, CI/CD, Docker, and production deployment", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When a bug appears and you're not sure if it's a frontend, backend, or data issue, how confident are you in isolating it?",
        "category": "Cross-Layer Debugging",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I'd struggle to know where to look", "5": "I trace requests end-to-end across network, server, and client"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex full-stack application you've worked on?",
        "category": "Project Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't built a full-stack app", "score": 1},
            {"value": "tutorial", "label": "To-do list or CRUD app from a tutorial", "score": 2},
            {"value": "personal", "label": "Multi-feature app with auth and real data I designed myself", "score": 4},
            {"value": "production", "label": "Team project or production app with users", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal as a full-stack developer in the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: land a full-stack job, go freelance, build and launch my own product, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning full-stack development?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


_MOBILE_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you building mobile app screens with proper navigation and state management?",
        "category": "Mobile UI & State",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I haven't built a mobile app before", "score": 1},
            {"value": "basic", "label": "I followed a tutorial to build a simple app", "score": 2},
            {"value": "mid", "label": "I can build multi-screen apps with navigation, forms, and API integration", "score": 4},
            {"value": "adv", "label": "I ship apps with complex state, animations, offline support, and platform APIs", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which mobile frameworks or platforms have you used?",
        "category": "Mobile Platforms",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "None yet", "score": 1},
            {"value": "basic", "label": "Experimented with Flutter, React Native, or SwiftUI", "score": 2},
            {"value": "mid", "label": "Built a multi-screen app with one framework and published or deployed it", "score": 4},
            {"value": "adv", "label": "Published apps to App Store or Play Store with native integrations", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When a mobile app crashes or behaves differently on another device, how confident are you in finding the cause?",
        "category": "Mobile Debugging",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I'd be stuck", "5": "I use device logs, profilers, and platform-specific debugging tools"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex mobile app you've worked on?",
        "category": "Project Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't built a mobile app", "score": 1},
            {"value": "tutorial", "label": "Counter or calculator from a tutorial", "score": 2},
            {"value": "personal", "label": "An app with multiple screens, API calls, and local storage", "score": 4},
            {"value": "production", "label": "Published app with real users or team collaboration", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal as a mobile developer in the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: build and publish my first app, learn Flutter or Swift, get a mobile dev job, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning mobile development?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


_DEVOPS_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How comfortable are you with deploying and managing applications in production?",
        "category": "Deployment & Operations",
        "dimension": "technical_depth",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I've never deployed an application", "score": 1},
            {"value": "basic", "label": "I've deployed to Heroku, Vercel, or a simple VPS", "score": 2},
            {"value": "mid", "label": "I use Docker, set up CI/CD pipelines, and manage servers", "score": 4},
            {"value": "adv", "label": "I manage Kubernetes clusters, infrastructure as code, and monitoring stacks", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "Which DevOps tools and platforms have you used?",
        "category": "DevOps Tooling",
        "dimension": "tooling",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "Just basic Git", "score": 1},
            {"value": "basic", "label": "Docker and a CI service (GitHub Actions, GitLab CI)", "score": 2},
            {"value": "mid", "label": "Docker Compose, Terraform or Ansible, and a cloud provider (AWS/GCP/Azure)", "score": 4},
            {"value": "adv", "label": "Kubernetes, monitoring (Prometheus/Grafana), secrets management, multi-env pipelines", "score": 5},
        ],
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "When a production service goes down at 2 AM, how confident are you in diagnosing and recovering it?",
        "category": "Incident Response",
        "dimension": "problem_solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "I wouldn't know where to start", "5": "I check metrics, logs, rollback, and write a post-mortem"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "What's the most complex infrastructure you've managed?",
        "category": "Infrastructure Complexity",
        "dimension": "experience",
        "estimated_seconds": 40,
        "options": [
            {"value": "none", "label": "I haven't managed infrastructure", "score": 1},
            {"value": "basic", "label": "A single server or PaaS deployment", "score": 2},
            {"value": "mid", "label": "Multi-service setup with Docker, a database, and a reverse proxy", "score": 4},
            {"value": "production", "label": "Production cluster with auto-scaling, monitoring, and automated rollbacks", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What's your primary goal as a DevOps engineer in the next 6 months?",
        "category": "Career Goal",
        "dimension": "goals",
        "estimated_seconds": 60,
        "helper": "For example: get AWS certified, learn Kubernetes, transition from backend to DevOps, automate my team's deployments, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How many hours per week can you realistically dedicate to learning DevOps?",
        "category": "Weekly Commitment",
        "dimension": "commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "< 3 hours", "3": "5–10 hours", "5": "15+ hours"},
    },
]


# ============================================================================
# CAREER QUESTION BANK REGISTRY
# ============================================================================

CAREER_QUESTION_BANKS: Dict[str, List[Dict[str, Any]]] = {
    "backend": _BACKEND_QUESTIONS,
    "frontend": _FRONTEND_QUESTIONS,
    "data_science": _DATA_SCIENCE_QUESTIONS,
    "fullstack": _FULLSTACK_QUESTIONS,
    "mobile": _MOBILE_QUESTIONS,
    "devops": _DEVOPS_QUESTIONS,
}


def _resolve_career_key(target_career: str) -> str:
    """Map a free-form career string to a question bank key."""
    lowered = (target_career or "").lower()
    if "backend" in lowered:
        return "backend"
    if "frontend" in lowered or "front-end" in lowered or "front end" in lowered:
        return "frontend"
    if "data" in lowered or "scientist" in lowered or "analyst" in lowered or "machine learning" in lowered:
        return "data_science"
    if "fullstack" in lowered or "full stack" in lowered or "full-stack" in lowered:
        return "fullstack"
    if "mobile" in lowered or "flutter" in lowered or "ios" in lowered or "android" in lowered:
        return "mobile"
    if "devops" in lowered or "dev ops" in lowered or "sre" in lowered or "infrastructure" in lowered or "cloud" in lowered:
        return "devops"
    return "backend"  # safe default


def get_default_questions(target_career: str = "") -> List[Dict[str, Any]]:
    """Return the deterministic career-specific fallback question set."""
    key = _resolve_career_key(target_career)
    return copy.deepcopy(CAREER_QUESTION_BANKS.get(key, _BACKEND_QUESTIONS))


# ============================================================================
# PROMPTS
# ============================================================================

QUESTION_SYSTEM_PROMPT = """You personalize career assessment questions for a career-development platform.

INPUT: You receive a bank of 6 questions for a specific career path.
TASK:
  - Personalize the wording of each question and its option labels to better match the target career and any extra user context.
  - You may adjust option labels to be more career-specific.
  - Do NOT change question IDs, types, interaction_modes, dimensions, categories, scoring, or estimated_seconds.
  - Do NOT add or remove questions. Return exactly 6.

OUTPUT: Return strict JSON with a top-level "questions" array containing 6 question objects.
Each question must preserve: id, type, interaction_mode, category, dimension, estimated_seconds.
For multiple_choice questions, preserve the options array structure with value, label, and score.
"""


EVALUATION_SYSTEM_PROMPT = """You evaluate career assessment responses for a career-development platform.

The user answered 6 questions covering these dimensions:
1. Core Technical depth (weight: 25%)
2. Tooling/Ecosystem knowledge (weight: 15%)
3. Problem-Solving approach (weight: 20%)
4. Experience level (weight: 20%)
5. Goal clarity (weight: 10%)
6. Learning commitment (weight: 10%)

SCORING RUBRIC:
- overall_score: 0–100, computed as a weighted sum of dimension scores.
- skill_scores: An object mapping each dimension name to a 0–100 score.
  Keys must be: "technical_depth", "tooling", "problem_solving", "experience", "goals", "commitment".
- strengths: Array of 2–3 specific strengths evidenced by the answers. Be concrete, not generic.
- areas_for_improvement: Array of 2–3 specific gaps evidenced by the answers. Reference actual skill areas.
- recommended_careers: Array of top 2 career paths. Each item: {"title": str, "match_score": int 0-100, "reasoning": str}.
  The first must be the target career. The second should be an adjacent role.
- recommended_learning_paths: Array of top 3 skills to prioritize.
  Each item: {"skill": str, "priority": "high"|"medium", "resources": []}.
- ai_insights: 2–3 sentence personalized analysis. Reference the user's specific answers.
- ai_confidence_score: Your confidence in this evaluation, 50–95.

Return strict JSON. No markdown fences, no explanation text outside the JSON.
"""


# ============================================================================
# NORMALIZERS
# ============================================================================

def _normalize_questions(raw_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, raw_question in enumerate(raw_questions[:6], start=1):
        question = dict(raw_question)
        question["id"] = int(question.get("id") or index)
        question["type"] = question.get("type") or "text"
        question["interaction_mode"] = question.get("interaction_mode") or question["type"]
        question["question"] = str(question.get("question") or "").strip()
        question["category"] = str(question.get("category") or "General").strip()
        question["dimension"] = str(question.get("dimension") or "technical_depth").strip()
        question["estimated_seconds"] = int(question.get("estimated_seconds") or 45)
        if question["question"]:
            normalized.append(question)

    return normalized


# ============================================================================
# AI SERVICE
# ============================================================================

class AssessmentAIService:
    """AI-backed assessment generation and evaluation with deterministic fallback."""

    QUESTION_FALLBACK_VERSION = "assessment-questions-bank-v2"
    EVALUATION_VERSION = "assessment-eval-gemma-v2"

    @staticmethod
    def generate_questions(assessment: Assessment) -> Tuple[List[Dict[str, Any]], GemmaResponse | None]:
        """Generate career-specific questions, personalizing via Gemma when available."""
        target_career = assessment.target_career or "Software Engineer"
        bank_questions = get_default_questions(target_career)

        client = GemmaClient()
        prompt = (
            f"Assessment type: {assessment.assessment_type}\n"
            f"Target career: {target_career}\n"
            f"Base questions to personalize:\n{json.dumps(bank_questions, indent=2)}\n\n"
            "Personalize the wording for this career while keeping the exact structure."
        )

        try:
            result = client.generate_structured(
                prompt=prompt,
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
            )
            questions = _normalize_questions(result.payload.get("questions", []) if result.payload else [])
            if len(questions) >= 4:
                return questions, result
        except Exception:
            pass

        # Fallback: career-specific bank questions (already good, not generic)
        return bank_questions, None

    @staticmethod
    def evaluate_assessment(assessment: Assessment) -> AssessmentAnalysisResult:
        """Evaluate user responses: try Gemma first, then fall back to baseline."""
        target_career = assessment.target_career or "Software Engineer"

        baseline = BaselineAssessmentAnalyzer.analyze(
            AssessmentAnalysisInput(
                assessment_id=str(assessment.id),
                assessment_type=assessment.assessment_type,
                target_career=target_career,
                responses=assessment.responses or [],
            )
        )

        prompt = (
            f"Target career: {target_career}\n"
            f"Assessment type: {assessment.assessment_type}\n\n"
            f"Questions:\n{json.dumps(assessment.questions, indent=2)}\n\n"
            f"User responses:\n{json.dumps(assessment.responses, indent=2)}\n\n"
            f"Dimension weights: {json.dumps(DIMENSION_WEIGHTS)}\n\n"
            "Evaluate these responses using the rubric and return structured JSON."
        )

        try:
            result = GemmaClient().generate_structured(
                prompt=prompt,
                system=EVALUATION_SYSTEM_PROMPT,
                required_keys=(
                    "overall_score",
                    "skill_scores",
                    "strengths",
                    "areas_for_improvement",
                    "recommended_careers",
                    "recommended_learning_paths",
                    "ai_insights",
                    "ai_confidence_score",
                ),
            )
            payload = result.payload or {}
            return AssessmentAnalysisResult(
                overall_score=Decimal(str(payload.get("overall_score", baseline.overall_score))),
                skill_scores=payload.get("skill_scores") or baseline.skill_scores,
                strengths=payload.get("strengths") or baseline.strengths,
                areas_for_improvement=payload.get("areas_for_improvement") or baseline.areas_for_improvement,
                recommended_careers=payload.get("recommended_careers") or baseline.recommended_careers,
                recommended_learning_paths=payload.get("recommended_learning_paths") or baseline.recommended_learning_paths,
                ai_insights=str(payload.get("ai_insights") or baseline.ai_insights),
                ai_confidence_score=Decimal(str(payload.get("ai_confidence_score", baseline.ai_confidence_score or 75))),
                metadata=build_ai_metadata(
                    source="llm",
                    processing_time_ms=result.metadata.processing_time_ms,
                    model=result.metadata.model,
                    provider=result.metadata.provider,
                    version=AssessmentAIService.EVALUATION_VERSION,
                    trace_id=result.metadata.trace_id,
                ),
            )
        except Exception as error:
            return AssessmentAnalysisResult(
                overall_score=baseline.overall_score,
                skill_scores=baseline.skill_scores,
                strengths=baseline.strengths,
                areas_for_improvement=baseline.areas_for_improvement,
                recommended_careers=baseline.recommended_careers,
                recommended_learning_paths=baseline.recommended_learning_paths,
                ai_insights=baseline.ai_insights,
                ai_confidence_score=baseline.ai_confidence_score,
                metadata=build_ai_metadata(
                    source="fallback",
                    processing_time_ms=baseline.metadata.processing_time_ms,
                    model=BaselineAssessmentAnalyzer.MODEL_NAME,
                    provider="sha8alny",
                    version=BaselineAssessmentAnalyzer.VERSION,
                    fallback_used=True,
                    error_code=type(error).__name__,
                ),
            )
