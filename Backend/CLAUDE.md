# CLAUDE.md - Backend

This file provides backend-specific guidance for the Sha8lny Django application.

**For project-level overview**, see the root `../CLAUDE.md`

## Backend Status

**Current Phase**: Phases 0-5 Complete - Gemini AI integration across all core modules
**Total Tests**: 274 passing
**Database**: SQLite (development), PostgreSQL (production ready)

### Completed Modules
- ✅ **Users**: Auth (JWT + Auth0), profiles, skills CRUD, demo seeder
- ✅ **Assessments**: staged AI question generation (8 roles), scoring engine + chains, role-graph taxonomy (curated-v3), coverage enforcement
- ✅ **Roadmaps**: AI generation from assessment with deterministic, assessment-aware fallback (roadmap.sh + O*NET grounded), course embedding match
- ✅ **Jobs**: search, skill matching, LightGBM ranking, Wuzzuf/CSV ingest, experience-level resolution
- ✅ **Advisory**: Gemini chat grounded in user context + career-knowledge RAG
- ✅ **Assessment Scenario RAG Corpus** (spec `005-scenario-rag-corpus`): role-aware, schema-validated few-shot examples retrieved per blueprint from a local Chroma collection. Layered after the existing static few-shot block in `apps/assessments/ai_pipeline.py:_build_stage_prompt`. Default-off (`ASSESSMENT_SCENARIO_RAG_ENABLED=false`); ships with a 10-scenario backend seed converted from `BACKEND_FALLBACK_SCENARIOS`. Authoring under `apps/assessments/scenario_corpus/`; rebuild via `manage.py rebuild_scenario_index`; audit via `manage.py scenario_corpus_audit`.

### Partial Modules
- 🟡 **Progress**, **Notifications** (email/push stubbed), **Career Tools** (PDF export is v2), **Courses** (route disabled)

## Project Overview

**Sha8alny** is an AI-powered career development platform that provides personalized learning roadmaps, skill assessments, course recommendations, and job market insights. The backend is built using Django with a **modular monolithic architecture**, using the Gemini API (default) with an optional local Ollama fallback for intelligent career guidance.

**Architecture**: Modular Monolith
- Single Django application with clear module boundaries
- Shared database (single source of truth)
- Direct Python imports between modules (no HTTP overhead)
- Service layer pattern for business logic
- ACID transactions across modules

## Commands

### Development Server
```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Run development server
python manage.py runserver

# Access admin panel
http://localhost:8000/admin/
```

### Database Migrations
```bash
# Create migrations for specific app
python manage.py makemigrations <app_name>

# Create migrations for all apps
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/users/tests/

# Run specific test file
pytest apps/users/tests/test_models.py

# Run specific test function
pytest apps/users/tests/test_models.py::test_user_creation

# Run Django shell for testing models
python manage.py shell
```

### Code Quality
```bash
# Format code with Black (max line length 100)
black apps/

# Lint with Flake8
flake8 apps/

# Sort imports with isort
isort apps/

# Type checking with mypy
mypy apps/
```

### Celery (Background Tasks)
```bash
# Start Celery worker (separate terminal)
celery -A config worker --loglevel=info

# Start Celery beat scheduler (separate terminal)
celery -A config beat --loglevel=info

# For development on Windows, use:
celery -A config worker --loglevel=info --pool=solo
```

### System Check
```bash
# Run Django system check
python manage.py check

# Check deployment readiness
python manage.py check --deploy
```

## Architecture

### Settings Structure

The project uses **split settings** architecture for environment-specific configurations:

- **`config/settings/base.py`**: Common settings for all environments (database, installed apps, middleware)
- **`config/settings/development.py`**: Development settings (DEBUG=True, SQLite database, CORS allow all)
- **`config/settings/production.py`**: Production settings (security hardening, PostgreSQL, Redis caching)

**Environment switching**: Set `DJANGO_SETTINGS_MODULE` in `.env` file:
```bash
# Development (default)
DJANGO_SETTINGS_MODULE=config.settings.development

# Production
DJANGO_SETTINGS_MODULE=config.settings.production
```

### Modular Monolith Structure

All application modules are in the `apps/` directory. Each module is a Django app:

```
apps/
├── core/              # Shared base models, exceptions, utilities
├── users/             # User management, Auth0 integration, skills
├── assessments/       # AI skill assessments, career evaluations
├── roadmaps/          # Personalized learning roadmap generation
├── courses/           # Course aggregation from multiple platforms
├── jobs/              # Job scraping, market analysis
├── progress/          # Learning progress tracking, milestones
├── career_tools/      # Resume builder, portfolio tools
└── notifications/     # Email, push, real-time notifications
```

**Key Characteristics**:
- All modules share a single database
- Modules communicate via direct Python imports (no HTTP)
- Can use `@transaction.atomic` across multiple modules
- Service layer separates business logic from views

**IMPORTANT**: All apps use the `apps.` prefix in their `apps.py` configuration:
```python
# apps/users/apps.py
class UsersConfig(AppConfig):
    name = "apps.users"  # NOT just "users"
```

### Cross-Module Communication

**Monolith Advantage**: Direct function calls between modules

```python
# In assessments module, call roadmap module directly
from django.db import transaction
from apps.roadmaps.services import RoadmapService

@transaction.atomic  # Single ACID transaction across both modules!
def complete_assessment_and_generate_roadmap(assessment_id):
    assessment = Assessment.objects.get(id=assessment_id)
    assessment.status = 'completed'
    assessment.save()

    # Direct Python call - no HTTP overhead!
    roadmap = RoadmapService.generate_from_assessment(
        user=assessment.user,
        assessment=assessment
    )
    return roadmap
```

### BaseModel Pattern

All models inherit from `apps.core.models.BaseModel`, which provides:

- **UUID primary keys**: `id = models.UUIDField(primary_key=True, default=uuid.uuid4)`
- **Timestamps**: `created_at`, `updated_at` (auto-managed)
- **Soft delete**: `is_deleted`, `deleted_at` (logical deletion)
- **Dual managers**:
  - `objects` - Returns only non-deleted records (default)
  - `all_objects` - Returns all records including soft-deleted

**Usage**:
```python
from apps.core.models import BaseModel

class Assessment(BaseModel):
    # Automatically gets: id, created_at, updated_at, is_deleted, deleted_at
    user = models.ForeignKey(...)
    # ... other fields

# Querying
Assessment.objects.all()        # Only non-deleted
Assessment.all_objects.all()    # Including soft-deleted

# Soft delete
assessment.delete()              # Sets is_deleted=True
assessment.delete(hard=True)     # Actual database deletion
assessment.restore()             # Undo soft delete
```

### Custom User Model

The project uses a custom User model (`apps.users.models.User`) with:

- **Auth0 integration**: `auth0_id` field for external authentication
- **Custom manager**: `apps.users.managers.UserManager`
- **USERNAME_FIELD**: `email` (not username)
- **Age validation**: Minimum 13 years old via `validate_age()` function

**Always reference User model via**:
```python
from django.conf import settings
user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
# NOT: from apps.users.models import User (in ForeignKeys)
```

### JSONB Fields for Flexible Data

Many models use `JSONField` for dynamic, nested data structures (works with both SQLite and PostgreSQL):

```python
# Assessment questions (flexible structure)
questions = models.JSONField(default=list)
# Example: [{"id": 1, "question": "...", "type": "multiple_choice", "options": [...]}]

# AssessmentResult skill scores (nested categories)
skill_scores = models.JSONField(default=dict)
# Example: {"technical": {"python": 90, "sql": 85}, "soft": {"communication": 88}}
```

**Why JSONB**: Different assessment types, AI recommendations, and dynamic content require schema flexibility without migrations.

### Exception Handling

All custom exceptions are defined in `apps/core/exceptions.py`:

```python
from apps.core.exceptions import (
    Sha8alnyException,          # Base exception
    AIServiceError,             # LLM API failures
    AssessmentProcessingError,  # Assessment errors
    RoadmapGenerationError,     # Roadmap errors
    ExternalAPIError,           # Third-party API errors
    ScrapingError,              # Web scraping errors
)
```

Use `custom_exception_handler` in DRF for standardized error responses.

### Database Configuration

**Development**: Uses **SQLite** (`db.sqlite3`) for fast iteration, zero setup
**Production**: Uses **PostgreSQL** with connection pooling, JSONB support

**Why SQLite in dev**:
- No server installation required
- Single file database (easy reset: `rm db.sqlite3`)
- Instant migrations
- Perfect for rapid model development

**Switch to PostgreSQL locally**: Change `DJANGO_SETTINGS_MODULE` to `config.settings.production` in `.env`

### AI/LLM Integration

AI processing is tracked extensively in models:

```python
# Assessment model
ai_processing_status = models.CharField(...)  # pending/processing/completed/failed
ai_processed_at = models.DateTimeField(...)
ai_processing_error = models.TextField(...)

# AssessmentResult model
llm_model_used = models.CharField(...)        # "gpt-4", "claude-3", etc.
llm_prompt_tokens = models.IntegerField(...)
llm_completion_tokens = models.IntegerField(...)
processing_time_seconds = models.DecimalField(...)
```

**LLM tasks should be run via Celery** (asynchronous) to avoid blocking API requests.

## Coding Standards

### Model Development

1. **Always inherit from BaseModel** (not `models.Model`)
2. **Add comprehensive help_text** to all fields for admin clarity
3. **Use CHOICES for status fields** (defined as class attributes)
4. **Add database indexes** on frequently queried fields:
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['user'], name='idx_model_user'),
           models.Index(fields=['status'], name='idx_model_status'),
       ]
   ```
5. **Implement `__str__()` and `__repr__()`** methods
6. **Add `@property` methods** for calculated fields (completion_percentage, age, etc.)

### Admin Configuration

Every model should have a corresponding admin class with:

- **List display**: Show key fields in admin list view
- **List filters**: Enable filtering by status, dates, categories
- **Search fields**: Enable search by user email, username, names
- **Readonly fields**: Mark non-editable fields (id, timestamps, calculated fields)
- **Autocomplete fields**: Use `autocomplete_fields` for ForeignKeys to improve performance
- **Fieldsets**: Organize fields into logical sections
- **Custom display methods**: Add color-coding, formatting for better UX

### Migrations

When creating migrations:

```bash
# ALWAYS create migrations for specific app to avoid conflicts
python manage.py makemigrations <app_name>

# NEVER run makemigrations without specifying app unless intentional
```

After adding/modifying models:
1. Create migrations
2. Apply migrations
3. Test in Django shell
4. Run `python manage.py check`

### Testing in Django Shell

Quick model testing pattern:

```python
python manage.py shell

from apps.users.models import User
from apps.assessments.models import Assessment, AssessmentResult

# Get test user
user = User.objects.first()

# Create test data
assessment = Assessment.objects.create(
    user=user,
    assessment_type='skills',
    # ... other fields
)

# Test properties
print(assessment.completion_percentage)
print(assessment.is_complete)

# Test relationships
print(assessment.has_result)
```

### Type Hints

Use type hints for function signatures:

```python
from typing import List, Dict, Optional
from uuid import UUID
from apps.users.models import User

def generate_roadmap(
    user_id: UUID,
    assessment_results: Dict[str, any],
    target_career: str
) -> Dict[str, any]:
    """Generate personalized learning roadmap."""
    pass

def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve user by email or None."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_skill_score(responses: List[Dict], difficulty: str = "medium") -> float:
    """
    Calculate skill score from assessment responses.

    Args:
        responses: List of user responses with question_id and answer
        difficulty: Assessment difficulty level

    Returns:
        Calculated skill score between 0-100

    Raises:
        ValidationError: If responses are invalid
    """
    pass
```

### Import Order

Follow this import order (enforced by `isort`):

```python
# 1. Standard library
import os
from datetime import date, timedelta

# 2. Third-party packages
from django.db import models
from rest_framework import serializers

# 3. Local application imports
from apps.users.models import User
from apps.core.models import BaseModel
from apps.core.exceptions import AIServiceError
```

## Key Patterns

### Soft Delete Pattern

```python
# Soft delete (preferred)
user.delete()  # Sets is_deleted=True, deleted_at=now()

# Hard delete (use with caution)
user.delete(hard=True)  # Actually removes from database

# Restore
user.restore()  # Sets is_deleted=False, deleted_at=None

# Query only active records (automatic)
User.objects.all()  # is_deleted=False

# Query including deleted records
User.all_objects.all()  # All records
```

### JSONB Data Pattern

Store flexible nested data in JSONB fields:

```python
# Assessment questions - array of objects
questions = [
    {"id": 1, "question": "Rate Python skills", "type": "scale", "options": [1,2,3,4,5]},
    {"id": 2, "question": "Years of experience?", "type": "number"}
]

# Skill scores - nested categories
skill_scores = {
    "technical": {"python": 90, "javascript": 75, "sql": 85},
    "soft": {"communication": 88, "teamwork": 92}
}

# AI recommendations - array of structured objects
recommended_careers = [
    {"title": "Backend Developer", "match_score": 92, "reasoning": "..."},
    {"title": "Data Engineer", "match_score": 88, "reasoning": "..."}
]
```

### Service Layer Pattern (Future)

While not yet implemented, services should follow this pattern:

```python
# apps/assessments/services.py
class AssessmentService:
    """Business logic for assessments."""

    @staticmethod
    def generate_questions(user_id: UUID, career: str) -> Dict:
        """Generate AI-powered assessment questions."""
        pass

    @staticmethod
    def process_results(assessment_id: UUID) -> AssessmentResult:
        """Process assessment and generate AI insights."""
        pass
```

Keep views thin - move business logic to services.

## Important Notes

### Do NOT

- Commit `.env` file (use `.env.example` as template)
- Hard-code API keys or secrets in code
- Use `User` model directly in ForeignKeys (use `settings.AUTH_USER_MODEL`)
- Delete database records without soft delete (unless absolutely necessary)
- Run `makemigrations` without specifying app name
- Create models without inheriting from `BaseModel`
- Skip `help_text` on model fields

### Always

- Use virtual environment (`venv/`)
- Run system check after model changes (`python manage.py check`)
- Test models in Django shell before committing
- Add indexes to frequently queried fields
- Use `@property` for calculated fields (don't store in database)
- Wrap user-facing strings with `_()` for i18n
- Use `Decimal` for monetary/score values (not `Float`)
- Track LLM token usage for cost monitoring

## Reference Documentation

- Full architecture: `docs/ARCHITECTURE.md`
- Database schema: `docs/DATABASE_SCHEMA.md`
- Coding standards: `docs/CODING_STANDARDS.md`
- Tech stack details: `docs/TECH_STACK.md`
- Backend README: `Backend/README.md`
