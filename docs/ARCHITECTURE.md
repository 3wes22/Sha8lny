# Sha8alny - System Architecture

## Overview
Sha8alny follows a **modular monolithic architecture** designed for rapid development, maintainability, and future scalability. This document outlines the high-level system design, module boundaries, data flow, and integration patterns.

---

## Architecture Philosophy

### Modular Monolith Approach

**What is a Modular Monolith?**
- Single deployable application
- Organized into logical domain modules (Django apps)
- Shared database with strong consistency
- Direct Python function calls between modules (no HTTP overhead)
- Can be extracted into microservices later if needed

**Why Modular Monolith for Sha8alny?**

✅ **Rapid Development**: Single codebase, no inter-service protocols
✅ **ACID Transactions**: Update multiple domains atomically
✅ **Lower Latency**: Direct function calls instead of HTTP
✅ **Simpler Deployment**: One application, one database
✅ **Cost Effective**: Single server for MVP
✅ **Easier Debugging**: Everything in one place
✅ **Future-Proof**: Can refactor to microservices if needed

### Key Principles
1. **Clear Module Boundaries**: Each Django app owns its domain logic
2. **Service Layer Pattern**: Business logic separated from views
3. **Shared Database**: Single source of truth with ACID guarantees
4. **Direct Function Calls**: Modules call each other via Python imports
5. **Async Processing**: Heavy tasks (AI, scraping) handled by Celery

### When to Consider Microservices (Future)
Only extract services when you have:
- Clear scaling bottlenecks (e.g., AI processing needs 10x more resources)
- Team size >10 developers needing independent deploys
- Regulatory requirements for data isolation
- Proven need for polyglot persistence

**Current Status**: Monolith is optimal for MVP and initial growth phase

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         React + TypeScript (Next.js)                     │   │
│  │  • User Interface                                        │   │
│  │  • Client-side routing                                   │   │
│  │  • State management (Context/Redux)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/REST/GraphQL
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO MONOLITH (Backend)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Django REST Framework (API Layer)                │   │
│  │  • Authentication (Auth0 + JWT)                          │   │
│  │  • Rate limiting                                         │   │
│  │  • CORS handling                                         │   │
│  │  • API versioning (v1, v2)                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              APPLICATION MODULES (Django Apps)           │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  Users   │  │Assessments│ │ Roadmaps │               │   │
│  │  │  Module  │  │  Module   │ │  Module  │               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │ Courses  │  │ Advisory │ │   Jobs   │               │   │
│  │  │  Module  │  │ (Chatbot)│ │  Module  │               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │ Progress │  │ Career   │  │Notifications│            │   │
│  │  │  Module  │  │  Tools   │  │  Module   │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  │                                                          │   │
│  │  • Modules communicate via direct Python imports        │   │
│  │  • Shared database (single source of truth)             │   │
│  │  • Service layer for business logic                     │   │
│  │  • Selector layer for optimized queries                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Core Infrastructure                    │   │
│  │  • BaseModel (UUID, timestamps, soft delete)            │   │
│  │  • Custom exceptions & error handling                   │   │
│  │  • Shared validators & utilities                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA & CACHE LAYER                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL  │  │    Redis     │  │   Pinecone   │           │
│  │  (Primary)   │  │   (Cache &   │  │  (Vectors)   │           │
│  │              │  │    Broker)   │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  BACKGROUND PROCESSING LAYER                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Celery Workers + Beat                       │   │
│  │  • AI processing (assessment analysis, roadmap gen)      │   │
│  │  • Job scraping tasks                                    │   │
│  │  • Course API fetching                                   │   │
│  │  • Email notifications                                   │   │
│  │  • Scheduled data cleanup                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES LAYER                      │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │   LLM    │  │   Job    │  │  Course  │  │  Auth0   │         │
│  │   APIs   │  │Platforms │  │Platforms │  │          │         │
│  │(OpenAI,  │  │ (Wuzzuf, │  │ (Udemy,  │  │          │         │
│  │Anthropic)│  │  Bayt)   │  │Coursera) │  │          │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Modules Breakdown

### 1. Users Module
**Responsibility:** User management, authentication, and profiles

**Capabilities:**
- User registration and login
- Profile management (name, skills, preferences)
- User preferences and settings
- Account verification
- Password management
- Auth0 integration
- JWT token generation and validation

**Models:**
- User (custom user model)
- Skill (master skills taxonomy)
- UserSkill (user's skill proficiency)
- UserPreferences (user settings)

**API Endpoints:**
- `POST /api/v1/users/register`
- `POST /api/v1/users/login`
- `GET /api/v1/users/profile`
- `PUT /api/v1/users/profile`
- `GET /api/v1/users/skills`
- `POST /api/v1/users/skills`

**Technology:**
- Django ORM
- Auth0 SDK
- Redis (session cache)

---

### 2. Assessments Module
**Responsibility:** AI-powered skill assessment and evaluation

**Capabilities:**
- Generate assessment questions based on career goals
- Process user responses
- Evaluate skill levels using AI models
- Generate skill gap analysis
- Provide assessment insights and recommendations
- Support both quick assessment and detailed assessment

**Processing:**
- **Background Processing**: Yes (via Celery)
- Assessment generation is CPU-intensive
- AI model inference takes time
- Results stored and cached

**Models:**
- Assessment (assessment instance with questions/responses)
- AssessmentResult (AI-analyzed results with skill scores)

**API Endpoints:**
- `POST /api/v1/assessments/start` - Initiate assessment
- `GET /api/v1/assessments/{id}/questions` - Get questions
- `POST /api/v1/assessments/{id}/submit` - Submit answers
- `GET /api/v1/assessments/{id}/results` - Get results (async)
- `GET /api/v1/assessments/{id}/insights` - Get skill insights

**Technology:**
- Celery workers for AI processing
- LangChain for LLM orchestration
- Multiple LLM providers (OpenAI, Anthropic)

**AI Integration:**
- Custom prompts for assessment generation
- Multi-model approach for different question types
- Embeddings for skill matching
- RAG for domain knowledge

**Cross-Module Communication:**
```python
# Direct Python import (monolith advantage)
from apps.users.models import User
from apps.assessments.services import AssessmentService

user = User.objects.get(id=user_id)
assessment = AssessmentService.create_assessment(user, 'skills')
```

---

### 3. Roadmaps Module
**Responsibility:** Generate and manage personalized learning roadmaps

**Capabilities:**
- Generate personalized learning paths based on assessment results
- Provide pre-built learning paths for common careers
- Structure roadmap into phases/milestones
- Recommend course sequences
- Adjust roadmaps based on progress
- Timeline estimation

**Processing:**
- **Background Processing**: Yes (via Celery)
- Roadmap generation is complex and time-consuming
- AI model orchestration across multiple calls
- RAG for course knowledge

**Models:**
- RoadmapTemplate (pre-built templates)
- Roadmap (user-specific roadmaps)
- RoadmapPhase (high-level phases)
- RoadmapMilestone (specific milestones)
- RoadmapCourse (courses assigned to milestones)

**API Endpoints:**
- `POST /api/v1/roadmaps/generate` - Generate custom roadmap (async)
- `GET /api/v1/roadmaps/templates` - Get pre-built paths
- `GET /api/v1/roadmaps/{id}` - Get roadmap details
- `PUT /api/v1/roadmaps/{id}/adjust` - Adjust based on progress
- `GET /api/v1/roadmaps/user/{user_id}` - Get user's roadmap

**Technology:**
- Celery workers
- LangChain for multi-step AI workflows
- Pinecone for course vector search
- Multiple LLM providers

**AI Workflow:**
```
Assessment Results → Skill Gap Analysis → Career Requirements →
Course Search (RAG) → Sequencing Logic (AI) → Timeline Estimation →
Personalized Roadmap
```

**Cross-Module Communication:**
```python
# Monolith allows atomic transactions across modules
from django.db import transaction
from apps.assessments.models import Assessment
from apps.roadmaps.services import RoadmapService

@transaction.atomic
def complete_assessment_and_generate_roadmap(assessment_id):
    assessment = Assessment.objects.select_for_update().get(id=assessment_id)
    assessment.status = 'completed'
    assessment.save()

    # Direct service call - no HTTP overhead!
    roadmap = RoadmapService.generate_from_assessment(
        user=assessment.user,
        assessment=assessment
    )
    return roadmap
```

---

### 4. Courses Module
**Responsibility:** Aggregate and manage learning resources from external platforms

**Capabilities:**
- Fetch courses from Udemy, Coursera, YouTube, etc.
- Real-time course API calls (minimal caching)
- Course metadata management
- Search and filter courses
- Course categorization by skill

**Processing:**
- **Background Processing**: Yes (via Celery)
- Periodic course catalog updates
- API rate limiting management

**Models:**
- CoursePlatform (Udemy, Coursera, etc.)
- Course (course metadata)
- CourseSkill (course-skill mappings)

**API Endpoints:**
- `GET /api/v1/courses/search` - Search courses
- `GET /api/v1/courses/{id}` - Get course details
- `GET /api/v1/courses/by-skill/{skill_id}` - Courses for skill
- `POST /api/v1/courses/bulk-fetch` - Batch fetch courses

**Technology:**
- External platform APIs (Udemy, Coursera, YouTube)
- Redis for rate limiting
- Celery for background updates

**Note:** Course data is fetched in real-time to ensure freshness

---

### 5. Advisory Module (AI Chatbot)
**Responsibility:** Provide context-aware career advisory through an AI chatbot

**Capabilities:**
- AI-powered conversational interface
- Context-aware responses using RAG (Retrieval-Augmented Generation)
- Personalized career guidance
- Roadmap-specific advice
- Assessment interpretation
- Job search guidance
- Conversation history management

**Processing:**
- **Background Processing**: Optional (streaming responses)
- Real-time LLM inference
- Context retrieval from user profile, roadmaps, and assessments
- Vector similarity search for relevant knowledge

**Models:**
- Conversation (chat sessions)
- Message (user and AI messages)

**API Endpoints:**
- `POST /api/v1/advisory/chat` - Send message and get AI response
- `GET /api/v1/advisory/conversations` - List user conversations
- `GET /api/v1/advisory/conversations/{id}` - Get conversation history
- `DELETE /api/v1/advisory/conversations/{id}` - Delete conversation
- `POST /api/v1/advisory/conversations/{id}/continue` - Continue existing conversation

**Technology:**
- LangChain for RAG pipeline
- OpenAI GPT-4 / Anthropic Claude for responses
- Vector database (Pinecone/Weaviate) for semantic search
- WebSocket support for streaming responses
- Redis for context caching

**RAG Pipeline:**
```
User Query → Context Retrieval (User Profile, Roadmap, Assessment) →
Vector Search (Career Knowledge Base, Courses) →
Prompt Construction →
LLM Generation →
Response Streaming (WebSocket)
```

**Context Sources:**
- User profile and career goals
- Latest assessment results and skill gaps
- Current roadmap and progress
- Relevant courses and job postings
- Career knowledge base (embedded documents)

**Cross-Module Integration:**
```python
from apps.users.models import User
from apps.assessments.models import Assessment
from apps.roadmaps.models import Roadmap
from apps.advisory.services import AdvisoryService

# Gather context from multiple modules
user = User.objects.get(id=user_id)
assessment = Assessment.objects.filter(user=user).latest('created_at')
roadmap = Roadmap.objects.filter(user=user).latest('created_at')

# Generate context-aware response
response = AdvisoryService.chat(
    user=user,
    message="How can I improve my Python skills?",
    context={
        'assessment': assessment,
        'roadmap': roadmap,
        'career_goal': user.preferences.target_career
    }
)
```

**Features:**
- ✅ Multi-turn conversations
- ✅ Context persistence across messages
- ✅ RAG for accurate, personalized responses
- ✅ Token usage tracking
- ✅ Response quality feedback (ratings)
- ✅ Conversation topics (general, roadmap, assessment, jobs)

---

### 6. Jobs Module
**Responsibility:** Job market analysis and job matching

**Capabilities:**
- Scrape job listings from Egyptian job platforms
- API integration when available
- Job data aggregation and cleaning
- Job-skill matching
- Market demand analysis
- Trending skills identification
- Job recommendations for users

**Processing:**
- **Background Processing**: Yes (via Celery)
- Scheduled scraping (daily/hourly)
- Data cleaning and normalization
- Skill extraction from job descriptions

**Models:**
- JobPlatform (Wuzzuf, Bayt, LinkedIn)
- Job (job listings)
- JobSkill (required skills)
- MarketInsight (market analytics)

**API Endpoints:**
- `GET /api/v1/jobs/search` - Search jobs
- `GET /api/v1/jobs/{id}` - Job details
- `GET /api/v1/jobs/recommendations` - Jobs matching user profile
- `GET /api/v1/jobs/market-insights` - Market analysis
- `GET /api/v1/jobs/trending-skills` - Hot skills

**Technology:**
- Scrapy for web scraping
- Selenium/Playwright for JS-heavy sites
- Celery Beat (scheduled tasks)

**Scraping Targets:**
- Wuzzuf (Egypt)
- Bayt (Regional)
- LinkedIn (Fallback)

**Caching Strategy:**
- Job listings cached for **24 hours**
- Market insights cached for **7 days**

---

### 7. Progress Module
**Responsibility:** Track user progress through learning roadmaps

**Capabilities:**
- Track course completion
- Milestone achievements
- Skill mastery progress
- Time tracking
- Progress analytics
- Generate progress reports

**Real-time Updates:**
- **WebSocket Support**: Yes (via Django Channels)
- Live progress updates to frontend
- Real-time milestone notifications

**Models:**
- UserProgress (overall progress)
- CourseCompletion (completed courses)
- MilestoneAchievement (achieved milestones)
- TimeLog (time tracking)

**API Endpoints:**
- `GET /api/v1/progress/user/{user_id}` - Overall progress
- `POST /api/v1/progress/course/{course_id}/complete` - Mark course done
- `GET /api/v1/progress/roadmap/{roadmap_id}` - Roadmap progress
- `GET /api/v1/progress/analytics` - Progress analytics
- `WS /ws/progress/{user_id}` - WebSocket for real-time updates

**Technology:**
- Django Channels (WebSockets)
- Redis (pub/sub for WebSocket)

---

### 8. Career Tools Module
**Responsibility:** Resume builder, portfolio, and ATS optimization

**Capabilities:**
- Resume/CV creation
- ATS-optimized CV generation
- Portfolio builder
- Template management
- Export to PDF/DOCX

**Models:**
- Resume (user resumes)
- Portfolio (user portfolios)

**API Endpoints:**
- `POST /api/v1/career-tools/resume/create`
- `GET /api/v1/career-tools/resume/{id}`
- `PUT /api/v1/career-tools/resume/{id}`
- `POST /api/v1/career-tools/resume/{id}/ats-optimize`
- `GET /api/v1/career-tools/resume/{id}/export`

**Technology:**
- PDF generation libraries (ReportLab)
- DOCX generation (python-docx)
- AI for ATS optimization

---

### 9. Notifications Module
**Responsibility:** User notifications via multiple channels

**Capabilities:**
- Email notifications
- In-app notifications
- Real-time push notifications (future)

**Models:**
- Notification (notification records)
- NotificationPreference (user preferences)

**API Endpoints:**
- `GET /api/v1/notifications` - Get user notifications
- `PUT /api/v1/notifications/{id}/read` - Mark as read
- `PUT /api/v1/notifications/preferences` - Update preferences

---

### 10. Core Module
**Responsibility:** Shared utilities, base models, exceptions

**Components:**
- **BaseModel**: UUID primary keys, timestamps, soft delete
- **Custom Exceptions**: Standardized error handling
- **Validators**: Reusable validation logic
- **Mixins**: Shared model behaviors
- **Utilities**: Common helper functions

**Usage:**
```python
from apps.core.models import BaseModel
from apps.core.exceptions import AIServiceError
from apps.core.validators import validate_age

class MyModel(BaseModel):  # Inherits UUID, timestamps, soft delete
    pass
```

---

## Service Layer Pattern (Critical for Monolith)

### Why Service Layer?

In monolithic architecture, **service layer separates business logic from views**:

```
View (HTTP) → Service (Business Logic) → Model (Data) → Database
                  ↓
            Other Services
                  ↓
            External APIs
                  ↓
            Celery Tasks
```

### Implementation Pattern

```python
# apps/assessments/services.py
class AssessmentService:
    """Business logic for assessments."""

    @staticmethod
    def create_assessment(user: User, assessment_type: str) -> Assessment:
        """
        Create new assessment with validation.

        Benefits of service layer:
        - Business logic is reusable (from views, tasks, commands)
        - Testable without HTTP layer
        - Can call other services directly
        - Atomic transactions across modules
        """
        # Validate user can take assessment
        if Assessment.objects.filter(user=user, status='in_progress').exists():
            raise ValidationError("Complete existing assessment first")

        # Create assessment
        assessment = Assessment.objects.create(
            user=user,
            assessment_type=assessment_type,
            total_questions=20,
            status='draft'
        )

        return assessment

    @staticmethod
    @transaction.atomic
    def complete_assessment(assessment_id: UUID) -> AssessmentResult:
        """Complete assessment and trigger roadmap generation."""
        assessment = Assessment.objects.get(id=assessment_id)
        assessment.status = 'completed'
        assessment.save()

        # Process results (triggers Celery task)
        result = AssessmentResultService.process(assessment)

        # Call roadmap service directly (monolith advantage!)
        from apps.roadmaps.services import RoadmapService
        if assessment.user.preferences.auto_generate_roadmap:
            RoadmapService.generate_from_assessment_async(
                user=assessment.user,
                assessment=assessment
            )

        return result

# apps/assessments/views.py (DRF)
class AssessmentViewSet(viewsets.ModelViewSet):
    """Assessment API - Thin views that delegate to services."""

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start new assessment."""
        serializer = StartAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Delegate to service
        assessment = AssessmentService.create_assessment(
            user=request.user,
            assessment_type=serializer.validated_data['assessment_type']
        )

        return Response(AssessmentSerializer(assessment).data, status=201)
```

### Selector Layer Pattern (Query Optimization)

Separate read operations for performance:

```python
# apps/assessments/selectors.py
class AssessmentSelector:
    """Query logic for assessments."""

    @staticmethod
    def get_user_assessments(user: User) -> QuerySet[Assessment]:
        """Get all assessments with optimized query."""
        return Assessment.objects.filter(
            user=user
        ).select_related('user').prefetch_related('result').order_by('-created_at')

    @staticmethod
    def get_assessment_with_details(assessment_id: UUID) -> Assessment:
        """Get assessment with all related data in single query."""
        return Assessment.objects.select_related(
            'user', 'result'
        ).prefetch_related(
            'user__skills', 'user__preferences'
        ).get(id=assessment_id)
```

---

## Data Flow Patterns

### 1. User Registration & Onboarding Flow
```
User → Frontend → Django API (DRF)
                        ↓
                  UserService.create_user()
                        ↓
                  Auth0 Verification
                        ↓
                  PostgreSQL (User)
                        ↓
                  JWT Token Generated
                        ↓
                  Frontend (Logged In)
```

### 2. Assessment & Roadmap Generation Flow
```
User Starts Assessment → Frontend → Django API
                                        ↓
                              AssessmentService.create_assessment()
                                        ↓
                              PostgreSQL (Assessment)
                                        ↓
User Submits Responses → Frontend → Django API
                                        ↓
                              AssessmentService.submit()
                                        ↓
                              Celery Task (Background AI Processing)
                                        ↓
                              LLM APIs (OpenAI/Anthropic)
                                        ↓
                              AssessmentResult Created
                                        ↓
                              RoadmapService.generate_from_assessment()
                                        ↓
                              Celery Task (AI Roadmap Generation)
                                        ↓
                              LLM + RAG (Pinecone)
                                        ↓
                              Roadmap Created
                                        ↓
                              WebSocket → Frontend (Real-time Update)
```

### 3. Cross-Module Transaction (Monolith Advantage)
```python
from django.db import transaction

@transaction.atomic
def complete_milestone_and_update_progress(milestone_id, user_id):
    """
    Complete milestone and update all related records atomically.

    In microservices: Would need distributed transaction or eventual consistency
    In monolith: Single ACID transaction across all tables!
    """
    # Update milestone
    milestone = RoadmapMilestone.objects.select_for_update().get(id=milestone_id)
    milestone.is_completed = True
    milestone.completed_at = timezone.now()
    milestone.save()

    # Update progress
    progress = UserProgress.objects.get(user_id=user_id)
    progress.milestones_completed += 1
    progress.save()

    # Update roadmap completion percentage
    roadmap = milestone.roadmap
    roadmap.completion_percentage = calculate_completion(roadmap)
    roadmap.save()

    # Create notification
    Notification.objects.create(
        user_id=user_id,
        type='milestone_completed',
        data={'milestone_id': milestone_id}
    )

    # All succeed or all rollback!
```

---

## Database Strategy

### Single Shared Database

**Approach:** One PostgreSQL database, all modules access it

**Benefits:**
- ✅ ACID transactions across modules
- ✅ No data duplication
- ✅ Simple foreign keys across modules
- ✅ Easy to query across domains
- ✅ No eventual consistency issues

**Schema Organization:**
- All tables in single database
- Logical grouping by module (users_*, assessments_*, roadmaps_*)
- Django migrations manage schema

**Example Foreign Keys:**
```python
# apps/roadmaps/models.py
class Roadmap(BaseModel):
    user = models.ForeignKey('users.User', ...)  # Cross-module FK
    assessment = models.ForeignKey('assessments.Assessment', ...)  # Cross-module FK
```

### Migration Strategy
```bash
# Create migrations for all modules
python manage.py makemigrations

# Apply all migrations atomically
python manage.py migrate
```

---

## Caching Strategy

### What to Cache

**1. User Sessions**
- **Storage**: Redis
- **TTL**: 24 hours
- **Reason**: Fast authentication checks

**2. Job Listings**
- **Storage**: Redis
- **TTL**: 24 hours
- **Reason**: Balance freshness vs API costs

**3. AI Responses (Selective)**
- **Storage**: Redis
- **TTL**: 7-30 days
- **Reason**: Reduce LLM costs for similar queries
- **Cache**: Pre-built roadmap templates, common assessment questions
- **Don't Cache**: Personalized assessments/roadmaps

**4. Market Insights**
- **Storage**: Redis
- **TTL**: 7 days
- **Reason**: Aggregated data changes slowly

### Cache Invalidation
- **Time-based (TTL)**: Automatic expiration
- **Event-based**: Clear cache on data updates
- **Manual**: Admin interface for urgent updates

---

## Background Processing Architecture

### Celery Setup

**Components:**

**1. Celery Workers**
- Execute background tasks
- Horizontally scalable
- Different queues for different task types

**Worker Queues:**
```
- ai-queue: Heavy AI processing (assessment, roadmap)
- scraper-queue: Job/course scraping
- default-queue: Misc tasks
```

**2. Celery Beat**
- Task scheduler (cron-like)
- Trigger periodic tasks

**Scheduled Tasks:**
- Job scraping: Every 6 hours
- Course metadata refresh: Daily
- Market insights calculation: Daily
- Cleanup old data: Weekly

**3. Message Broker (Redis)**
- Task queue storage
- Result backend
- Pub/sub for WebSockets

### Task Example
```python
# apps/assessments/tasks.py
from celery import shared_task

@shared_task(queue='ai-queue')
def process_assessment_results(assessment_id):
    """Process assessment with AI (runs in background)."""
    from apps.assessments.services import AssessmentResultService
    return AssessmentResultService.process(assessment_id)

# Called from service
from apps.assessments.tasks import process_assessment_results
process_assessment_results.delay(str(assessment_id))
```

---

## Real-Time Communication (WebSockets)

### Django Channels Architecture

**Use Cases:**
1. Progress updates (live course completion)
2. Notifications (instant delivery)
3. Community chat (future)

**Components:**
- **Channel Layer (Redis)**: Message passing
- **ASGI Server (Daphne)**: Handle WebSocket connections
- **WebSocket Consumers**: Send/receive messages

### WebSocket Flow
```
Frontend (WebSocket Client)
      ↓
Django Channels (ASGI)
      ↓
Redis Channel Layer (Pub/Sub)
      ↓
Background Service (Publishes Event)
```

---

## API Design Strategy

### RESTful APIs (Primary)

**Endpoint Pattern:**
```
GET    /api/v1/{module}/{resource}
POST   /api/v1/{module}/{resource}
GET    /api/v1/{module}/{resource}/{id}
PUT    /api/v1/{module}/{resource}/{id}
DELETE /api/v1/{module}/{resource}/{id}
```

**Technology:** Django REST Framework

### API Versioning

**Important:** Version from day 1
```python
# config/urls.py
urlpatterns = [
    path('api/v1/users/', include('apps.users.api.v1.urls')),
    path('api/v1/assessments/', include('apps.assessments.api.v1.urls')),
    # v2 in future without breaking v1
]
```

---

## Security Architecture

### Authentication & Authorization

**Authentication Flow:**
```
1. User Login → Frontend
2. Frontend → Auth0 (Social/Email login)
3. Auth0 validates → Returns Auth0 token
4. Frontend → Django API (Auth0 token)
5. Django → Validates token → Generates JWT
6. JWT → Frontend (stored securely)
7. Subsequent Requests → Include JWT in headers
8. Django → Validates JWT → Process request
```

### API Security
- JWT tokens with short expiration
- HTTPS everywhere (TLS 1.3)
- CORS properly configured
- Rate limiting per user/IP
- Input validation at all layers
- SQL injection prevention (Django ORM)

---

## Deployment Architecture

### MVP Deployment (Single VPS)

```
┌────────────────────────────────────────┐
│          Hostinger VPS                 │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │         Nginx                    │ │
│  │  (Reverse Proxy + Static Files) │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │   Django Monolith (Gunicorn)    │ │
│  │   • All modules in one process  │ │
│  │   • Service layer architecture  │ │
│  │   • API versioning (v1)         │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │       PostgreSQL                │ │
│  │   (Single shared database)      │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │         Redis                   │ │
│  │   (Cache + Celery broker)       │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │   Celery Workers + Beat         │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

### Future Scaling (Horizontal)

```
                ┌─────────────┐
                │   Nginx LB  │
                └─────────────┘
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌───────────┐  ┌───────────┐  ┌───────────┐
│Django App1│  │Django App2│  │Django AppN│
│(Gunicorn) │  │(Gunicorn) │  │(Gunicorn) │
└───────────┘  └───────────┘  └───────────┘
        ↓              ↓              ↓
        └──────────────┼──────────────┘
                       ↓
            ┌──────────────────┐
            │PostgreSQL Primary│
            │     (Write)      │
            └──────────────────┘
                       ↓
            ┌──────────────────┐
            │PostgreSQL Replica│
            │     (Read)       │
            └──────────────────┘
```

---

## Monitoring & Observability

### Application Monitoring

**Logging:**
- Structured logs (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized logging (future: ELK stack)

**Metrics:**
- Request rate, latency, error rate
- Database connections, query time
- Celery queue length, task duration
- Cache hit/miss ratio

**Error Tracking:**
- Sentry for real-time error monitoring
- Stack traces with context
- Alert on critical errors

### AI/LLM Monitoring
- Token usage per request
- Model response times
- Cost tracking
- Quality metrics

---

## Development Roadmap

### Phase 1: Foundation (Current)
- ✅ Core infrastructure (BaseModel, exceptions)
- ✅ User module (authentication, profiles)
- ✅ Assessment module (models)
- ⏳ Roadmap module (models)
- ⏳ Remaining modules (models)

### Phase 2: Service Layer
- Add service layer to all modules
- Implement selectors for optimized queries
- Add comprehensive tests

### Phase 3: API Layer
- Build REST APIs with DRF
- Implement API versioning
- Add authentication & permissions

### Phase 4: Background Processing
- Implement Celery tasks
- Set up Celery Beat for scheduling
- Add task monitoring

### Phase 5: Real-time Features
- Implement WebSockets with Django Channels
- Add real-time progress updates
- Implement notification system

### Phase 6: Polish & Deploy
- Add comprehensive tests
- Performance optimization
- Deploy to production

---

## When to Consider Extracting Services (Future)

**Extract to separate service if:**
1. Module has >3x resource needs vs others (e.g., AI processing)
2. Module needs independent scaling
3. Module developed by separate team (>10 total devs)
4. Module has different deployment cadence
5. Regulatory requirements for data isolation

**Good candidates for future extraction:**
- **Assessment/Roadmap AI Processing**: CPU-intensive, scales independently
- **Job Scraping**: Memory-intensive, runs on schedule

**Keep in monolith:**
- User management (core to everything)
- Progress tracking (tightly coupled to roadmaps)
- Notifications (lightweight, tightly coupled)

---

## Technology Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React, TypeScript, Next.js |
| **Backend** | Django (Monolith), Django REST Framework |
| **Database** | PostgreSQL (Single shared database) |
| **Cache** | Redis |
| **Vector DB** | Pinecone |
| **Background Jobs** | Celery, Celery Beat, Redis |
| **Real-time** | Django Channels, Redis Channels Layer |
| **AI/ML** | LangChain, OpenAI, Anthropic |
| **Authentication** | Auth0, JWT |
| **Web Scraping** | Scrapy, Selenium, BeautifulSoup |
| **Monitoring** | Sentry, Prometheus (future), Grafana (future) |
| **Deployment** | Gunicorn, Nginx, Hostinger VPS |

---

*Last Updated: January 2025*
*Architecture: Modular Monolith - Optimized for rapid development and future scalability*
