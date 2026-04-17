# Sha8alny Backend

Backend API for the Sha8alny AI-powered career development platform.

**Architecture**: Modular Monolithic Django application

## Project Structure

```
Backend/
   config/                      # Django project configuration
      settings/
         __init__.py         # Settings loader
         base.py             # Base settings (common to all environments)
         development.py      # Development-specific settings
         production.py       # Production-specific settings
      __init__.py
      asgi.py                 # ASGI configuration (for WebSockets)
      urls.py                 # Root URL configuration
      wsgi.py                 # WSGI configuration
   apps/                        # Application modules (Django apps)
      users/                  # User management module
      assessments/            # AI skill assessment module
      roadmaps/               # Learning roadmap generation module
      courses/                # Course aggregation module
      advisory/               # AI chatbot & career advisory module
      jobs/                   # Job market analysis module
      progress/               # Progress tracking module
      career_tools/           # Resume builder & portfolio module
      notifications/          # Notification module
      core/                   # Shared utilities and base classes
   static/                      # Static files (CSS, JS, images)
   media/                       # User-uploaded files
   templates/                   # HTML templates
   logs/                        # Application logs
   utils/                       # Helper utilities
   .env.example                 # Environment variable template
   .gitignore                   # Git ignore rules
   requirements.txt             # Python dependencies
   manage.py                    # Django management script
   README.md                    # This file
```

## Technology Stack

- **Framework**: Django 5.0+
- **API**: Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Cache**: Django cache framework (`LocMemCache` by default in development, Redis in production)
- **Background Tasks**: Celery + Redis
- **Authentication**: JWT (Simple JWT) + Auth0
- **Real-time**: Django Channels (WebSockets)
- **AI/ML**: Local Gemma via Ollama, shared backend AI runtime, ChromaDB, sentence-transformers
- **Web Scraping**: Scrapy, Selenium, BeautifulSoup

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+ (optional for development, can use SQLite)
- Redis (recommended for Celery and production-like caching)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Sha8alny/Backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies plus the local ai-models package
pip install -r requirements.txt

# Pull the local Gemma model used by the backend AI runtime
ollama pull gemma4:e2b

# Copy environment variables
cp .env.example .env

# Edit .env and fill in your configuration
# At minimum, set SECRET_KEY and database credentials
```

### 3. Database Setup

**For Development (SQLite - Default)**:
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

**For PostgreSQL**:
```bash
# Create database
createdb sha8alny_db

# Update .env with PostgreSQL credentials
# Uncomment PostgreSQL configuration in config/settings/development.py

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
# Start Django development server
python manage.py runserver

# Server will be available at http://localhost:8000
```

### 5. Run Celery (Background Tasks)

In a separate terminal:

```bash
# Start Celery worker
celery -A config worker --loglevel=info

# Start Celery beat (scheduled tasks)
celery -A config beat --loglevel=info
```

### 6. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/users/tests/
```

## Configuration

### Environment Variables

Key environment variables (see .env.example for full list):

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Database credentials
- `REDIS_URL`: Redis connection URL
- `DJANGO_CACHE_BACKEND`: Django cache backend path. Defaults to `django.core.cache.backends.locmem.LocMemCache` when unset.
- `OLLAMA_HOST`: Ollama base URL (defaults to `http://127.0.0.1:11434`)
- `OLLAMA_MODEL`: Local model name (defaults to `gemma4:e2b`; override to `gemma4:e4b` on stronger hardware)
- `CHROMA_PERSIST_DIR`: Optional Chroma persistence directory

### Local AI Runtime

The active AI architecture is local-first:

- backend AI features call Ollama through `Backend/apps/core/gemma_client.py`
- the backend imports `rag` and other helpers from the editable local `ai-models/` package
- advisory, assessment, and roadmap flows no longer rely on OpenAI, Anthropic, LangChain, or Pinecone
- staged `skills` assessments use at most 3 LLM calls per completed run: stage 1 generation, stage 2 generation, and final evaluation

If you need the architecture rationale, start with `docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md`.

### Settings Modules

The project uses split settings:

- **base.py**: Common settings for all environments
- **development.py**: Development-specific settings (DEBUG=True, SQLite, etc.)
- **production.py**: Production settings (security hardened)

To switch environments:

```bash
# Development (default)
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver
```

## API Documentation

Once the server is running, access API documentation at:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **Browsable API**: http://localhost:8000/api/

## Application Modules Overview

**Note**: Sha8alny uses a modular monolithic architecture. All modules are part of a single Django application with:
- Shared database (single source of truth)
- Direct Python imports between modules (no HTTP overhead)
- ACID transactions across modules
- Service layer for business logic

### 1. Users Module
**Responsibility**: User management, authentication, and profiles

**Features**:
- User registration and authentication
- Profile management
- Skills management
- Auth0 integration

**Models**: User, Skill, UserSkill, UserPreferences

### 2. Assessments Module
**Responsibility**: AI-powered skill assessment and evaluation

**Features**:
- AI-powered skill assessments
- Question generation using LLMs
- Skill gap analysis
- Assessment results processing (async via Celery)

**Models**: Assessment, AssessmentResult

### 3. Roadmaps Module
**Responsibility**: Generate and manage personalized learning roadmaps

**Features**:
- Personalized learning roadmap generation
- Pre-built career path templates
- Progress-based roadmap adjustments
- Timeline estimation

**Models**: RoadmapTemplate, Roadmap, RoadmapPhase, RoadmapMilestone, RoadmapCourse

### 4. Courses Module
**Responsibility**: Aggregate and manage learning resources

**Features**:
- Course aggregation from multiple platforms
- Real-time course API integration
- Course recommendations
- Search and filtering

**Models**: CoursePlatform, Course, CourseSkill

### 5. Advisory Module (AI Chatbot)
**Responsibility**: AI-powered career advisory chatbot

**Features**:
- Context-aware conversational AI
- RAG (Retrieval-Augmented Generation) for personalized advice
- Roadmap and assessment-specific guidance
- Job search assistance
- Conversation history management

**Models**: Conversation, Message

### 6. Jobs Module
**Responsibility**: Job market analysis and job matching

**Features**:
- Job market data scraping
- Job-skill matching
- Market insights and analytics
- Trending skills identification

**Models**: JobPlatform, Job, JobSkill, MarketInsight

### 7. Progress Module
**Responsibility**: Track user progress through learning roadmaps

**Features**:
- Learning progress tracking
- Milestone achievements
- Real-time updates via WebSockets
- Progress analytics

**Models**: UserProgress, CourseCompletion, MilestoneAchievement, TimeLog

### 8. Career Tools Module
**Responsibility**: Resume builder, portfolio, and ATS optimization

**Features**:
- Resume/CV builder
- ATS-optimized resume generation
- Portfolio builder
- PDF/DOCX export

**Models**: Resume, Portfolio

### 9. Notifications Module
**Responsibility**: User notifications via multiple channels

**Features**:
- Real-time notifications
- Email notifications
- Push notifications (future)

**Models**: Notification, NotificationPreference

### 10. Core Module
**Responsibility**: Shared utilities, base models, exceptions

**Components**:
- Shared utilities
- Custom exception handlers
- Base models and mixins (BaseModel with UUID, timestamps, soft delete)
- Common validators

## Development Workflow

### Creating a New App

```bash
cd apps
django-admin startapp <app_name>

# Update config/settings/base.py to include the app in LOCAL_APPS
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations
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
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Use PostgreSQL database
- [ ] Configure Redis for caching
- [ ] Set up SSL/HTTPS
- [ ] Configure email service
- [ ] Set up Sentry for error tracking
- [ ] Configure static file serving (WhiteNoise/CDN)
- [ ] Set up database backups
- [ ] Configure Celery workers
- [ ] Set up monitoring and logging

### Production Deployment (Hostinger VPS)

```bash
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

## Contributing

1. Follow [Coding Standards](../docs/CODING_STANDARDS.md)
2. Write tests for new features
3. Run code quality checks before committing
4. Create meaningful commit messages
5. Submit pull requests for review

## License

[Add your license here]

## Contact

For questions or support, contact [your-email@example.com]
