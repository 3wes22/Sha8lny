# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sha8lny** is an AI-powered career empowerment platform targeting the Egyptian job market. The platform provides personalized career guidance through AI-driven assessments, adaptive learning pathways, and integration with local industry data.

**Current Architecture**: Modular Monolithic Django application with a service layer pattern.

## Development Commands

### Environment Setup

```bash
# Navigate to backend
cd Backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env and configure SECRET_KEY, database credentials, and API keys
```

### Database Operations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Create superuser for admin access
python manage.py createsuperuser
```

### Running the Application

```bash
# Start development server (default: http://localhost:8000)
python manage.py runserver

# Run Celery worker (separate terminal)
celery -A config worker --loglevel=info

# Run Celery beat scheduler (separate terminal)
celery -A config beat --loglevel=info
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/users/tests/

# Run specific test file
pytest apps/users/tests/test_services.py

# Run specific test
pytest apps/users/tests/test_services.py::TestUserService::test_create_user
```

### Code Quality

```bash
# Format code with Black
black apps/

# Lint with Flake8
flake8 apps/

# Sort imports
isort apps/

# Type checking with mypy
mypy apps/

# Run all quality checks
black apps/ && isort apps/ && flake8 apps/ && mypy apps/
```

### Django Management

```bash
# Access Django shell
python manage.py shell

# Create new Django app
cd apps
django-admin startapp <app_name>
# Remember to add app to LOCAL_APPS in config/settings/base.py

# Collect static files (production)
python manage.py collectstatic --noinput
```

## Architecture Overview

### Modular Monolith Pattern

Sha8lny uses a **modular monolithic architecture** (NOT microservices). Key characteristics:

- **Single deployable application** with all modules in one Django project
- **Shared PostgreSQL database** with ACID transaction guarantees across modules
- **Direct Python function calls** between modules (no HTTP overhead)
- **Service layer pattern** separates business logic from API views
- **Can be extracted to microservices later** if specific scaling needs arise

**Why Modular Monolith?**
- Faster development (no inter-service protocols)
- Atomic cross-module transactions
- Lower latency (in-process calls)
- Simpler deployment and debugging
- Cost-effective for MVP phase

### Core Architectural Layers

```
┌─────────────────────────────────────────┐
│     Django REST Framework (API Layer)   │  ← API endpoints, authentication, rate limiting
├─────────────────────────────────────────┤
│       Service Layer (Business Logic)    │  ← Core business logic, reusable across views/tasks
├─────────────────────────────────────────┤
│         Model Layer (Data Access)       │  ← Django ORM, database models
├─────────────────────────────────────────┤
│      PostgreSQL (Single Database)       │  ← Shared data store with ACID guarantees
└─────────────────────────────────────────┘
```

### Module Communication Pattern

**CRITICAL**: Modules communicate via direct Python imports, NOT HTTP calls:

```python
# ✅ CORRECT: Direct service-to-service calls
from apps.users.models import User
from apps.assessments.services import AssessmentService

user = User.objects.get(id=user_id)
assessment = AssessmentService.create_assessment(user, 'skills')

# ✅ CORRECT: Atomic cross-module transactions
from django.db import transaction

@transaction.atomic
def complete_milestone_and_notify(milestone_id, user_id):
    # Updates roadmap, progress, and creates notification atomically
    milestone = RoadmapMilestone.objects.get(id=milestone_id)
    milestone.is_completed = True
    milestone.save()

    progress = UserProgress.objects.get(user_id=user_id)
    progress.milestones_completed += 1
    progress.save()

    Notification.objects.create(user_id=user_id, type='milestone_completed')
    # All succeed or all rollback - this is the monolith advantage!

# ❌ WRONG: Don't make HTTP calls between modules
# response = requests.post('http://localhost:8000/api/assessments/')  # NO!
```

## Application Modules

### 1. Users Module (`apps/users/`)
- User authentication and registration (Auth0 + JWT)
- Profile management and preferences
- Skills taxonomy and user skill tracking
- **Key Service**: `UserService`, `SkillService`

### 2. Assessments Module (`apps/assessments/`)
- AI-powered skill assessments
- Question generation using LLMs (OpenAI, Anthropic)
- Assessment result processing (async via Celery)
- Skill gap analysis
- **Key Service**: `AssessmentService`

### 3. Roadmaps Module (`apps/roadmaps/`)
- Personalized learning roadmap generation
- Pre-built career path templates
- Phase/milestone/course structuring
- Progress-based roadmap adjustments
- **Key Service**: `RoadmapService`

### 4. Courses Module (`apps/courses/`)
- Course aggregation from external platforms (Udemy, Coursera, YouTube)
- Real-time course API integration
- Course recommendations and search
- **Key Service**: `CourseService`

### 5. Advisory Module (`apps/advisory/`)
- AI chatbot for career guidance
- RAG (Retrieval-Augmented Generation) for personalized advice
- Conversation history management
- Context-aware responses using user data
- **Key Service**: `AdvisoryService`

### 6. Jobs Module (`apps/jobs/`)
- Job market data scraping (Wuzzuf, Bayt, LinkedIn)
- Job-skill matching
- Market insights and trending skills
- Scheduled scraping via Celery Beat
- **Key Service**: `JobService`

### 7. Progress Module (`apps/progress/`)
- Learning progress tracking
- Course completion and milestone achievements
- Real-time updates via WebSockets (Django Channels)
- **Key Service**: `ProgressService`

### 8. Career Tools Module (`apps/career_tools/`)
- Resume/CV builder
- ATS-optimized resume generation
- Portfolio builder with PDF/DOCX export
- **Key Service**: `ResumeService`, `PortfolioService`

### 9. Notifications Module (`apps/notifications/`)
- Multi-channel notifications (in-app, email, push)
- Notification preferences management
- Real-time delivery via signals and WebSockets
- **Key Service**: `NotificationService`

### 10. Core Module (`apps/core/`)
- **BaseModel**: UUID primary keys, timestamps, soft delete functionality
- **Custom exceptions**: `Sha8alnyException`, `AIServiceError`, etc.
- **Shared validators and utilities**
- All models should inherit from `BaseModel` for consistency

## Service Layer Pattern (CRITICAL)

**All business logic must be in the service layer**, not in views or models.

### Service Layer Structure

```python
# apps/<module>/services.py

class ExampleService:
    """Service for business logic operations"""

    @staticmethod
    def create_something(user: User, data: dict) -> Model:
        """
        Service methods are static and contain business logic.
        They can be called from:
        - Views (API endpoints)
        - Celery tasks (background jobs)
        - Management commands
        - Other services
        """
        # Validation
        if not data.get('required_field'):
            raise ValidationError("Required field missing")

        # Business logic
        instance = Model.objects.create(user=user, **data)

        # Call other services if needed (direct import)
        from apps.other_module.services import OtherService
        OtherService.do_something(instance)

        return instance

    @staticmethod
    @transaction.atomic
    def complex_operation(instance_id: UUID) -> dict:
        """Use @transaction.atomic for multi-model operations"""
        instance = Model.objects.select_for_update().get(id=instance_id)
        # ... atomic operations across multiple tables
        return {'status': 'success'}
```

### View Layer (Thin Controllers)

```python
# apps/<module>/views.py

class ExampleViewSet(viewsets.ModelViewSet):
    """Views delegate to services - keep them thin!"""

    @action(detail=False, methods=['post'])
    def custom_action(self, request):
        serializer = InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Delegate to service
        result = ExampleService.create_something(
            user=request.user,
            data=serializer.validated_data
        )

        return Response(OutputSerializer(result).data, status=201)
```

## Settings Architecture

The project uses **split settings** for different environments:

- `config/settings/base.py` - Common settings for all environments
- `config/settings/development.py` - Development settings (DEBUG=True, SQLite)
- `config/settings/production.py` - Production settings (DEBUG=False, PostgreSQL, security hardening)

**Switching environments**:

```bash
# Development (default)
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver
```

**Environment Variables** (`.env` file):
- `SECRET_KEY` - Django secret key (required)
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated allowed hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database credentials
- `REDIS_URL` - Redis connection URL
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic (Claude) API key
- `PINECONE_API_KEY` - Pinecone vector database API key

## Background Processing with Celery

### Task Structure

```python
# apps/<module>/tasks.py

from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, queue='ai-queue')
def process_something(self, instance_id: str) -> dict:
    """
    Background task for heavy processing.

    Args:
        instance_id: UUID string of the instance to process

    Returns:
        dict: Processing results
    """
    try:
        from apps.module.services import Service
        result = Service.process(instance_id)

        logger.info(f"Successfully processed {instance_id}")
        return {'status': 'success', 'result': result}

    except Exception as exc:
        logger.error(f"Error processing {instance_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Calling Tasks

```python
# From service or view
from apps.module.tasks import process_something

# Async execution
process_something.delay(str(instance_id))

# Get result (blocking)
result = process_something.apply_async(args=[str(instance_id)])
result.get(timeout=30)
```

### Celery Queues

- `ai-queue` - Heavy AI/LLM processing (assessment, roadmap generation)
- `scraper-queue` - Job/course scraping tasks
- `default` - Miscellaneous background tasks

## Database Model Conventions

### Always Inherit from BaseModel

```python
from apps.core.models import BaseModel

class MyModel(BaseModel):
    """
    BaseModel provides:
    - id: UUIDField (primary key)
    - created_at: DateTimeField (auto_now_add=True)
    - updated_at: DateTimeField (auto_now=True)
    - is_deleted: BooleanField (for soft deletes)
    - deleted_at: DateTimeField (nullable)
    """

    # Your fields here
    name = models.CharField(max_length=255)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'my_models'
        ordering = ['-created_at']
```

### Foreign Keys Across Modules

```python
# Use string references for cross-module foreign keys
user = models.ForeignKey('users.User', on_delete=models.CASCADE)
assessment = models.ForeignKey('assessments.Assessment', on_delete=models.SET_NULL, null=True)
```

## AI/LLM Integration

### LLM Service Usage

```python
from apps.ai.services import LLMService

# Initialize service
llm_service = LLMService()

# Generate content
response = llm_service.generate(
    prompt="Generate assessment questions for Python developer",
    model="gpt-4",  # or "claude-3-opus"
    temperature=0.7
)

# Use RAG for context-aware responses
from apps.ai.services import RAGService

rag_service = RAGService()
response = rag_service.query(
    query="How to improve Python skills?",
    context_data={'user_level': 'intermediate', 'target_role': 'Backend Developer'}
)
```

### Vector Search with Pinecone

```python
# Storing embeddings
from apps.ai.services import VectorService

vector_service = VectorService()
vector_service.upsert(
    id=str(course.id),
    vector=course_embedding,
    metadata={'title': course.title, 'category': course.category}
)

# Searching similar items
results = vector_service.search(
    query_vector=query_embedding,
    top_k=10,
    filter={'category': 'programming'}
)
```

## Testing Conventions

### Test File Structure

```python
# apps/<module>/tests/test_services.py

from django.test import TestCase
from apps.users.models import User
from apps.module.services import ExampleService

class ExampleServiceTestCase(TestCase):
    """Test cases for ExampleService"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

    def test_create_success(self):
        """Test successful creation"""
        result = ExampleService.create_something(
            user=self.user,
            data={'field': 'value'}
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.field, 'value')

    def test_create_validation_error(self):
        """Test validation error handling"""
        with self.assertRaises(ValidationError):
            ExampleService.create_something(
                user=self.user,
                data={}  # Missing required field
            )
```

## Important Implementation Notes

### Model Managers and QuerySets

When filtering data, always exclude soft-deleted records:

```python
# ✅ Good - excludes soft-deleted
User.objects.filter(is_deleted=False, email=email)

# ✅ Better - use custom manager method
class UserManager(models.Manager):
    def active(self):
        return self.filter(is_deleted=False)

User.objects.active().filter(email=email)
```

### Query Optimization

Always use `select_related()` and `prefetch_related()` to avoid N+1 queries:

```python
# ❌ Bad - N+1 query problem
users = User.objects.all()
for user in users:
    print(user.roadmap.title)  # Separate query per user

# ✅ Good - single query with JOIN
users = User.objects.select_related('roadmap').all()

# ✅ Good - for reverse FKs and many-to-many
roadmaps = Roadmap.objects.prefetch_related('phases__milestones').all()
```

### API Versioning

All API endpoints are versioned from day 1:

```python
# URL pattern
/api/v1/<module>/<resource>/

# Future v2 won't break v1
/api/v2/<module>/<resource>/
```

### Error Handling

Use custom exceptions defined in `apps/core/exceptions.py`:

```python
from apps.core.exceptions import AIServiceError, InsufficientDataError

def risky_operation():
    try:
        # ... operation
    except ExternalAPIError as e:
        raise AIServiceError(f"AI service failed: {str(e)}")
```

## Git Workflow

### Branch Naming

```
feature/{ticket-id}-{short-description}
bugfix/{ticket-id}-{short-description}
hotfix/{ticket-id}-{short-description}

Examples:
feature/SHA-123-user-authentication
bugfix/SHA-125-roadmap-calculation-error
```

### Commit Message Format

Follow Conventional Commits:

```
feat(assessment): add AI-powered question generation
fix(roadmap): correct completion percentage calculation
docs(api): update authentication endpoint documentation
refactor(users): extract skill logic to service layer
test(notifications): add service layer tests
```

## Common Pitfalls to Avoid

1. **Don't put business logic in views** - Use service layer
2. **Don't make HTTP calls between modules** - Use direct Python imports
3. **Don't forget soft delete checks** - Always filter `is_deleted=False`
4. **Don't skip select_related/prefetch_related** - Avoid N+1 queries
5. **Don't commit secrets** - Use environment variables
6. **Don't forget @transaction.atomic** - For multi-model operations
7. **Don't bypass the service layer** - Even in Celery tasks, use services

## API Documentation

Once the server is running, access API documentation at:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **Browsable API**: http://localhost:8000/api/

## Production Deployment

### Pre-deployment Checklist

```bash
# Set production environment variables
export DJANGO_SETTINGS_MODULE=config.settings.production
export DEBUG=False
export SECRET_KEY='<strong-secret-key>'

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Start Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Start Celery workers
celery -A config worker --loglevel=info --concurrency=4

# Start Celery beat
celery -A config beat --loglevel=info
```

## Technology Stack Summary

- **Backend Framework**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Cache & Message Broker**: Redis
- **Background Tasks**: Celery + Celery Beat
- **Real-time**: Django Channels (WebSockets)
- **AI/ML**: LangChain, OpenAI, Anthropic, Pinecone
- **Authentication**: Auth0 + JWT (djangorestframework-simplejwt)
- **Web Scraping**: Scrapy, Selenium, BeautifulSoup, Playwright
- **Testing**: pytest, pytest-django, pytest-cov
- **Code Quality**: black, flake8, mypy, isort
- **Production Server**: Gunicorn (WSGI) + Daphne (ASGI)
