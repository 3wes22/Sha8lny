# Sha8alny - System Architecture

## Overview
Sha8alny follows a **microservices architecture** designed for scalability, maintainability, and independent service deployment. This document outlines the high-level system design, service boundaries, data flow, and integration patterns.

---

## Architecture Philosophy

### Key Principles
1. **Service Independence**: Each service can be developed, deployed, and scaled independently
2. **API-First Design**: All services communicate through well-defined APIs
3. **Scalability**: Services can scale horizontally based on demand
4. **Resilience**: Service failures are isolated and don't cascade
5. **Technology Flexibility**: Services can use different tech stacks if beneficial

### Trade-offs
- **Complexity**: More complex than monolithic architecture
- **Network Overhead**: Inter-service communication latency
- **Data Consistency**: Eventual consistency vs immediate consistency
- **Deployment Complexity**: More moving parts to manage

**Decision**: Benefits of scalability and maintainability outweigh complexity for Sha8alny's ambitious feature set.

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
│  │  • State management                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/REST/GraphQL
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Gateway / Load Balancer                 │   │
│  │  • Request routing                                       │   │
│  │  • Authentication (Auth0 + JWT)                          │   │
│  │  • Rate limiting                                         │   │
│  │  • Request/Response transformation                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     MICROSERVICES LAYER                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   User       │  │  Assessment  │  │   Roadmap    │           │
│  │   Service    │  │   Service    │  │   Service    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Course     │  │     Job      │  │  Community   │           │
│  │   Service    │  │   Service    │  │   Service    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Progress   │  │    Career    │  │ Notification │           │
│  │   Service    │  │Tools Service │  │   Service    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA & CACHE LAYER                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL  │  │    Redis     │  │   Pinecone   │           │
│  │  (Primary)   │  │   (Cache)    │  │  (Vectors)   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  BACKGROUND PROCESSING LAYER                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Celery Workers + Beat                       │   │
│  │  • Job scraping tasks                                    │   │
│  │  • Course API fetching                                   │   │
│  │  • AI processing queue                                   │   │
│  │  • Assessment generation                                 │   │
│  │  • Roadmap generation                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES LAYER                      │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │   LLM    │  │   Job    │  │  Course  │  │  Auth0   │         │
│  │   APIs   │  │Platforms │  │Platforms │  │          │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Microservices Breakdown

### 1. User Service
**Responsibility:** User management, authentication, and profiles

**Capabilities:**
- User registration and login
- Profile management (name, skills, preferences)
- User preferences and settings
- Account verification
- Password management
- Auth0 integration
- JWT token generation and validation

**Database Schema:**
- Users table
- User skills (soft/hard)
- User preferences
- Authentication tokens

**API Endpoints:**
- `POST /api/users/register`
- `POST /api/users/login`
- `GET /api/users/profile`
- `PUT /api/users/profile`
- `GET /api/users/skills`
- `POST /api/users/skills`

**Technology:**
- Django + DRF
- PostgreSQL
- Auth0 SDK
- Redis (session cache)

---

### 2. Assessment Service
**Responsibility:** AI-powered skill assessment and evaluation

**Capabilities:**
- Generate assessment questions based on career goals
- Process user responses
- Evaluate skill levels using AI models
- Generate skill gap analysis
- Provide assessment insights and recommendations
- Support both quick assessment and detailed assessment

**Processing:**
- **Background Processing Required**: Yes (via Celery)
- Assessment generation is CPU-intensive
- AI model inference takes time
- Results stored and cached

**Database Schema:**
- Assessments table
- Assessment questions
- User responses
- Skill evaluations
- Assessment results

**API Endpoints:**
- `POST /api/assessments/start` - Initiate assessment
- `GET /api/assessments/{id}/questions` - Get questions
- `POST /api/assessments/{id}/submit` - Submit answers
- `GET /api/assessments/{id}/results` - Get results (async)
- `GET /api/assessments/{id}/insights` - Get skill insights

**Technology:**
- Django + DRF
- PostgreSQL
- Celery workers for AI processing
- LangChain for LLM orchestration
- Multiple LLM providers

**AI Integration:**
- Custom prompts for assessment generation
- Multi-model approach for different question types
- Embeddings for skill matching
- RAG for domain knowledge

---

### 3. Roadmap Service
**Responsibility:** Generate and manage personalized learning roadmaps

**Capabilities:**
- Generate personalized learning paths based on assessment results
- Provide pre-built learning paths for common careers
- Structure roadmap into phases/milestones
- Recommend course sequences
- Adjust roadmaps based on progress
- Timeline estimation

**Processing:**
- **Background Processing Required**: Yes (via Celery)
- Roadmap generation is complex and time-consuming
- AI model orchestration across multiple calls
- RAG for course knowledge

**Database Schema:**
- Roadmaps table
- Roadmap phases/milestones
- Roadmap skills
- User roadmaps (assigned)
- Pre-built templates

**API Endpoints:**
- `POST /api/roadmaps/generate` - Generate custom roadmap (async)
- `GET /api/roadmaps/templates` - Get pre-built paths
- `GET /api/roadmaps/{id}` - Get roadmap details
- `PUT /api/roadmaps/{id}/adjust` - Adjust based on progress
- `GET /api/roadmaps/user/{user_id}` - Get user's roadmap

**Technology:**
- Django + DRF
- PostgreSQL
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

---

### 4. Course Service
**Responsibility:** Aggregate and manage learning resources from external platforms

**Capabilities:**
- Fetch courses from Udemy, Coursera, YouTube, etc.
- Real-time course API calls (no caching)
- Course metadata management
- Search and filter courses
- Rate and review courses (future)
- Course categorization by skill

**Processing:**
- **Background Processing Required**: Yes (via Celery)
- Periodic course catalog updates
- API rate limiting management
- Metadata enrichment

**Database Schema:**
- Course catalog (metadata only, refreshed periodically)
- Course platforms
- Course-skill mappings
- Course ratings/reviews (future)

**API Endpoints:**
- `GET /api/courses/search` - Search courses (real-time)
- `GET /api/courses/{id}` - Get course details
- `GET /api/courses/by-skill/{skill_id}` - Courses for skill
- `POST /api/courses/bulk-fetch` - Batch fetch courses

**Technology:**
- Django + DRF
- PostgreSQL (minimal storage)
- Celery for background updates
- Redis for rate limiting
- External platform APIs

**External Integrations:**
- Udemy Affiliate API
- Coursera API
- YouTube Data API
- edX API
- Custom scrapers for platforms without APIs

**Note:** Course data is fetched in real-time to ensure freshness, not cached extensively.

---

### 5. Job Service
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
- **Background Processing Required**: Yes (via Celery)
- Scheduled scraping (daily/hourly)
- Data cleaning and normalization
- Skill extraction from job descriptions

**Database Schema:**
- Jobs table
- Job skills
- Job platforms
- Market insights
- Skill demand metrics

**API Endpoints:**
- `GET /api/jobs/search` - Search jobs
- `GET /api/jobs/{id}` - Job details
- `GET /api/jobs/recommendations` - Jobs matching user profile
- `GET /api/jobs/market-insights` - Market analysis
- `GET /api/jobs/trending-skills` - Hot skills

**Technology:**
- Django + DRF
- PostgreSQL
- Celery Beat (scheduled tasks)
- Scrapy for web scraping
- Selenium/Playwright for JS-heavy sites
- Proxy rotation for scalability

**Scraping Targets:**
- Wuzzuf (Egypt)
- Bayt (Regional)
- LinkedIn (Fallback)
- Other Egyptian platforms

**Caching Strategy:**
- Job listings cached for **24 hours** (balancing freshness vs API costs)
- Market insights cached for **7 days**
- Trending skills cached for **7 days**
- Individual job details cached for **24 hours**

---

### 6. Progress Service
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

**Database Schema:**
- User progress table
- Course completions
- Milestone achievements
- Time logs
- Progress snapshots

**API Endpoints:**
- `GET /api/progress/user/{user_id}` - Overall progress
- `POST /api/progress/course/{course_id}/complete` - Mark course done
- `GET /api/progress/roadmap/{roadmap_id}` - Roadmap progress
- `GET /api/progress/analytics` - Progress analytics
- `WS /ws/progress/{user_id}` - WebSocket for real-time updates

**Technology:**
- Django + DRF
- Django Channels (WebSockets)
- PostgreSQL
- Redis (pub/sub for WebSocket)

---

### 7. Career Tools Service
**Responsibility:** Resume builder, portfolio, and ATS optimization

**Capabilities:**
- Resume/CV creation
- ATS-optimized CV generation
- Portfolio builder
- Template management
- Export to PDF/DOCX

**Database Schema:**
- Resumes table (stored as database attributes)
- Portfolios table
- Templates
- User career documents

**API Endpoints:**
- `POST /api/career-tools/resume/create`
- `GET /api/career-tools/resume/{id}`
- `PUT /api/career-tools/resume/{id}`
- `POST /api/career-tools/resume/{id}/ats-optimize`
- `GET /api/career-tools/resume/{id}/export`
- `POST /api/career-tools/portfolio/create`

**Technology:**
- Django + DRF
- PostgreSQL (document storage)
- PDF generation libraries
- DOCX generation libraries
- AI for ATS optimization

**Note:** Files stored as database BLOBs initially, migration to S3 planned for scale.

---



## API Design Strategy

### Dual API Approach

**1. RESTful APIs**
- Primary API pattern for most services
- Standard CRUD operations
- Easy to understand and implement
- Good for mobile apps (future)

**Endpoints Pattern:**
```
GET    /api/v1/{service}/{resource}
POST   /api/v1/{service}/{resource}
GET    /api/v1/{service}/{resource}/{id}
PUT    /api/v1/{service}/{resource}/{id}
DELETE /api/v1/{service}/{resource}/{id}
```

**2. GraphQL API**
- Flexible data fetching for complex frontend needs
- Reduce over-fetching and under-fetching
- Single endpoint for multiple resources
- Better for dashboard and analytics views

**GraphQL Endpoint:**
```
POST /graphql
```

**Use Cases for GraphQL:**
- User dashboard (pull data from multiple services)
- Progress analytics (combine progress, courses, roadmap)
- Complex filtering and searching
- Nested data relationships

**Technology:**
- **REST**: Django REST Framework
- **GraphQL**: Graphene-Django

**Example GraphQL Query:**
```graphql
query UserDashboard($userId: ID!) {
  user(id: $userId) {
    profile {
      name
      skills
    }
    currentRoadmap {
      title
      progress
      milestones {
        title
        completed
      }
    }
    recentJobs {
      title
      company
      matchScore
    }
  }
}
```

---

## Data Flow Patterns

### 1. User Registration & Onboarding Flow
```
User → Frontend → API Gateway → User Service
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
User Starts Assessment → Frontend → API Gateway → Assessment Service
                                                         ↓
                                                  Celery Worker (Background)
                                                         ↓
                                                   LLM APIs (Multiple Calls)
                                                         ↓
                                                   Assessment Results
                                                         ↓
                                                   PostgreSQL
                                                         ↓
                                    Trigger → Roadmap Service (Celery)
                                                         ↓
                                            LLM + RAG (Pinecone for courses)
                                                         ↓
                                            Personalized Roadmap Generated
                                                         ↓
                                                   PostgreSQL
                                                         ↓
                                    WebSocket → Frontend (Real-time Update)
```

### 3. Course Recommendation Flow
```
User Request → Frontend → API Gateway → Course Service
                                              ↓
                                    Real-time API Calls
                                    (Udemy, Coursera, YouTube)
                                              ↓
                                    Data Aggregation & Filtering
                                              ↓
                                    Skill Matching (Pinecone)
                                              ↓
                                    Ranked Course List
                                              ↓
                                         Frontend
```

### 4. Job Market Analysis Flow (Background)
```
Celery Beat (Scheduler) → Job Service Worker
                                ↓
                    Web Scraping (Wuzzuf, Bayt, LinkedIn)
                                ↓
                    Data Cleaning & Normalization
                                ↓
                    Skill Extraction (NLP/LLM)
                                ↓
                    PostgreSQL (Jobs, Skills, Insights)
                                ↓
                    Redis Cache (24 hours)
```

### 5. Progress Tracking Flow (Real-time)
```
User Completes Course → Frontend → API Gateway → Progress Service
                                                        ↓
                                                  PostgreSQL Update
                                                        ↓
                                                  Redis Pub/Sub
                                                        ↓
                                    WebSocket → Frontend (Live Update)
                                                        ↓
                                    Check Milestones → Notification Service
                                                        ↓
                                    WebSocket → Frontend (Notification)
```

---

## Inter-Service Communication

### Synchronous Communication (REST/HTTP)
**When to Use:**
- Real-time user requests
- Data retrieval
- Simple service-to-service calls

**Example:**
```
Roadmap Service → Course Service (Get courses for skill)
Progress Service → Roadmap Service (Get roadmap details)
```

**Technology:** Django requests library, HTTP/REST

### Asynchronous Communication (Message Queue)
**When to Use:**
- Background processing
- Long-running tasks
- Event-driven updates
- Decoupled services

**Example:**
```
Assessment Complete (Event) → Roadmap Service (Generate roadmap)
Course Completed (Event) → Progress Service → Notification Service
```

**Technology:** 
- **Celery + Redis**: Task queue and message broker
- **RabbitMQ** (alternative): More robust message broker

### Event-Driven Architecture
**Events Published:**
- `user.registered`
- `assessment.completed`
- `roadmap.generated`
- `course.completed`
- `milestone.achieved`
- `job.matched`

**Event Flow:**
```
Service A → Redis Pub/Sub → Service B (Subscriber)
```

---

## Database Strategy

### Database per Service Pattern

**Principle:** Each microservice owns its database

**Benefits:**
- Service independence
- Technology flexibility
- Scalability
- Fault isolation

**Challenges:**
- Data consistency
- Cross-service queries
- Increased complexity

### Database Assignments

| Service | Database | Justification |
|---------|----------|---------------|
| User Service | PostgreSQL | Relational user data |
| Assessment Service | PostgreSQL | Structured assessment data |
| Roadmap Service | PostgreSQL | Complex relationships |
| Course Service | PostgreSQL (light) | Metadata only |
| Job Service | PostgreSQL | Structured job data |
| Progress Service | PostgreSQL | Time-series data |
| Career Tools Service | PostgreSQL | Document storage |
| Community Service | PostgreSQL | Relational comments/posts |
| Notification Service | PostgreSQL | Notification history |

**Shared Databases:**
- **Redis**: Shared cache layer across services (acceptable for caching)
- **Pinecone**: Shared vector database (acceptable for AI services)

### Data Consistency Patterns

**1. Eventual Consistency**
- Accept temporary inconsistencies
- Use events to propagate changes
- Example: User profile update → notify other services

**2. Saga Pattern (for distributed transactions)**
- Coordinate multi-service operations
- Rollback on failures
- Example: Generate roadmap (assessment + course + roadmap services)

**3. CQRS (Command Query Responsibility Segregation)**
- Separate read and write models
- Optimize for different access patterns
- Use for analytics/reporting

---

## Caching Strategy

### What to Cache

**1. User Sessions**
- **Storage**: Redis
- **TTL**: 24 hours (configurable)
- **Reason**: Fast authentication checks

**2. Job Listings**
- **Storage**: Redis
- **TTL**: 24 hours
- **Reason**: Balance between freshness and API costs
- **Invalidation**: Manual refresh or scheduled updates

**3. AI Responses (Consideration)**
- **Storage**: Redis or PostgreSQL
- **TTL**: 7-30 days depending on query type
- **Reason**: Reduce LLM costs for similar queries
- **Caution**: Ensure responses remain relevant

**Recommendation for AI Caching:**
- Cache assessment questions for common careers (30 days)
- Cache pre-built roadmap templates (indefinite, manual invalidation)
- Cache market insights (7 days)
- Don't cache personalized assessments/roadmaps (user-specific)

**4. Course Metadata (Minimal)**
- **Storage**: PostgreSQL + Redis
- **TTL**: Not cached (real-time API calls)
- **Reason**: Course availability and pricing change frequently

**5. Market Insights**
- **Storage**: Redis
- **TTL**: 7 days
- **Reason**: Aggregated data changes slowly

### Cache Invalidation Strategy

**Time-based (TTL):**
- Automatic expiration after set duration

**Event-based:**
- Clear cache when data updates occur
- Example: Job scraping completes → invalidate job cache

**Manual:**
- Admin interface to clear specific caches
- Use for debugging or urgent updates

---

## Authentication & Authorization Flow

### Authentication Process

```
1. User Login → Frontend
2. Frontend → Auth0 (Social/Email login)
3. Auth0 validates → Returns Auth0 token
4. Frontend → API Gateway (Auth0 token)
5. API Gateway → User Service (Verify token)
6. User Service → Generates JWT (custom claims)
7. JWT → Frontend (stored securely)
8. Subsequent Requests → Include JWT in headers
9. API Gateway → Validates JWT → Routes to services
10. Services → Trust JWT from API Gateway
```

### JWT Token Structure

```json
{
  "user_id": "12345",
  "email": "user@example.com",
  "roles": ["student"],
  "permissions": ["roadmap:read", "progress:write"],
  "exp": 1735689600,
  "iat": 1735603200
}
```

### Service-to-Service Authentication

**Option 1: Service Tokens**
- Each service has a unique token
- Used for inter-service communication

**Option 2: mTLS (Mutual TLS)**
- Certificate-based authentication
- More secure for production

**Current Approach**: Service tokens (simpler for MVP)

---

## API Gateway / Load Balancer

### Responsibilities

**1. Routing**
- Route requests to appropriate microservices
- URL-based routing (e.g., `/api/users/*` → User Service)

**2. Authentication**
- Validate JWT tokens
- Integrate with Auth0
- Block unauthorized requests

**3. Rate Limiting**
- Prevent abuse
- Per-user and per-IP limits
- Protect backend services

**4. Request/Response Transformation**
- Standardize response formats
- Add correlation IDs for tracing
- Error normalization

**5. CORS Handling**
- Allow frontend origins
- Manage preflight requests

**6. SSL Termination**
- Handle HTTPS
- Offload SSL from backend services

### Technology Options

**Option 1: Nginx**
- Lightweight and fast
- Good for simple routing
- Requires manual configuration

**Option 2: Kong**
- API Gateway with plugin ecosystem
- Built-in rate limiting, auth, logging
- More features, slightly heavier

**Option 3: AWS API Gateway / Google Cloud API Gateway**
- Managed service
- Auto-scaling
- Requires cloud migration

**Recommended for MVP**: Nginx + custom Django middleware for advanced features

---

## Background Processing Architecture

### Celery Setup

**Components:**

**1. Celery Workers**
- Execute background tasks
- Horizontally scalable
- Different worker types for different tasks

**Worker Types:**
```
- ai-workers: Heavy AI processing (assessment, roadmap)
- scraper-workers: Job/course scraping
- general-workers: Misc tasks
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
- Pub/sub for events

### Task Priority System

**High Priority:**
- User-initiated AI processing (assessment, roadmap)
- Real-time notifications

**Medium Priority:**
- Progress updates
- Data aggregation

**Low Priority:**
- Scheduled scraping
- Analytics generation
- Cleanup tasks

### Task Monitoring
- **Flower**: Web-based Celery monitoring
- Task status tracking
- Worker health monitoring
- Failed task retry logic

---

## Real-Time Communication (WebSockets)

### Django Channels Architecture

**Use Cases:**
1. **Progress Updates**: Live course completion updates
2. **Notifications**: Instant notification delivery
3. **Community**: Real-time chat/comments (future)

**Components:**

**1. Channel Layer (Redis)**
- Message passing between Django instances
- Pub/sub mechanism

**2. ASGI Server (Daphne/Uvicorn)**
- Handle WebSocket connections
- Async request handling

**3. WebSocket Consumers**
- Handle WebSocket connections
- Send/receive messages

### WebSocket Flow

```
Frontend (WebSocket Client)
      ↓
Nginx (WebSocket Proxy)
      ↓
Django Channels (ASGI)
      ↓
Redis Channel Layer (Pub/Sub)
      ↓
Background Service (Publishes Event)
```

**Example: Progress Update**
```python
# Progress Service publishes event
channel_layer.group_send(
    f"user_{user_id}",
    {
        "type": "progress.update",
        "data": {"course_id": 123, "status": "completed"}
    }
)

# WebSocket consumer receives and forwards to frontend
```

---

## Scalability Considerations

### Horizontal Scaling

**Stateless Services:**
- All microservices designed to be stateless
- Scale by adding more instances
- Load balancer distributes traffic

**Stateful Components:**
- **Database**: Read replicas, connection pooling
- **Redis**: Redis Cluster for high availability
- **Celery**: Add more workers as needed

### Performance Optimization

**1. Database Optimization**
- Proper indexing on frequently queried fields
- Connection pooling (PgBouncer)
- Query optimization
- Database monitoring

**2. Caching**
- Redis for hot data
- CDN for static assets (future)
- Browser caching headers

**3. API Optimization**
- Pagination for large result sets
- Field filtering (GraphQL shines here)
- Batch endpoints for multiple resources
- Async processing for heavy operations

**4. AI/LLM Optimization**
- Response caching for similar queries
- Batch processing when possible
- Use cheaper models for simple tasks
- Streaming responses for long generations

### Load Testing
- **Locust** or **JMeter**: Simulate traffic
- Test each service independently
- Test full system integration
- Identify bottlenecks early

---

## Resilience & Fault Tolerance

### Service Failure Handling

**1. Circuit Breaker Pattern**
- Detect failing services
- Stop sending requests temporarily
- Graceful degradation

**Example:** If Job Service is down, show cached job data with warning.

**2. Retry Logic**
- Exponential backoff for transient failures
- Max retry limits
- Dead letter queue for persistent failures

**3. Timeout Management**
- Set reasonable timeouts for service calls
- Prevent cascade failures

**4. Health Checks**
- Endpoint: `GET /health` on each service
- Load balancer uses health checks
- Auto-restart unhealthy services

### Data Backup & Recovery

**Database Backups:**
- Daily automated backups
- Point-in-time recovery capability
- Test restore procedures regularly

**Redis Persistence:**
- RDB snapshots (periodic)
- AOF (append-only file) for durability
- Balance performance vs durability

---

## Monitoring & Observability

### Application Monitoring

**1. Logging**
- Centralized logging (ELK stack or similar)
- Structured logs (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs across services

**2. Metrics**
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- Key metrics:
  - Request rate, latency, error rate
  - Database connections, query time
  - Celery queue length, task duration
  - Cache hit/miss ratio

**3. Tracing**
- **Jaeger** or **Zipkin**: Distributed tracing
- Track requests across multiple services
- Identify bottlenecks in service chains

**4. Error Tracking**
- **Sentry**: Real-time error monitoring
- Stack traces and context
- Alert on critical errors

### AI/LLM Monitoring

- Token usage per request
- Model response times
- Cost tracking
- Quality metrics (if applicable)
- LangSmith for LLM observability

---

## Security Architecture

### API Security

**1. Authentication**
- JWT tokens with short expiration
- Refresh token rotation
- Token revocation support

**2. Authorization**
- Role-based access control (RBAC)
- Endpoint-level permissions
- Service-to-service authorization

**3. Input Validation**
- Request validation at API Gateway
- Service-level validation (defense in depth)
- Sanitize user inputs

**4. Rate Limiting**
- Per-user limits
- Per-IP limits
- Protect against DDoS

**5. HTTPS Everywhere**
- TLS 1.3
- Certificate management (Let's Encrypt)
- HSTS headers

### Data Security

**1. Encryption**
- Data at rest: Database encryption
- Data in transit: TLS/SSL
- Sensitive fields: Application-level encryption

**2. Database Security**
- Principle of least privilege
- Separate database users per service
- Network isolation

**3. Secrets Management**
- Environment variables for config
- **Vault** (future): Centralized secret management
- Never commit secrets to Git

### AI Security

**1. Prompt Injection Prevention**
- Input sanitization
- Output validation
- System prompt protection

**2. API Key Security**
- Rotate keys regularly
- Separate keys per environment
- Monitor usage for anomalies

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
│  │   Django Services (Gunicorn)    │ │
│  │   • User Service                │ │
│  │   • Assessment Service          │ │
│  │   • Roadmap Service             │ │
│  │   • Course Service              │ │
│  │   • Job Service                 │ │
│  │   • Progress Service            │ │
│  │   • Career Tools Service        │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │       PostgreSQL                │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │         Redis                   │ │
│  └──────────────────────────────────┘ │
│              ↓                         │
│  ┌──────────────────────────────────┐ │
│  │   Celery Workers + Beat         │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

### Future Scaling (Multi-Server)

```
                    ┌─────────────┐
                    │   Nginx LB  │
                    └─────────────┘
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  App Server 1 │  │  App Server 2 │  │  App Server N │
│  (Services)   │  │  (Services)   │  │  (Services)   │
└───────────────┘  └───────────────┘  └───────────────┘
        ↓                  ↓                  ↓
        └──────────────────┼──────────────────┘
                           ↓
                ┌──────────────────────┐
                │  PostgreSQL Primary  │
                │  (Write)             │
                └──────────────────────┘
                           ↓
                ┌──────────────────────┐
                │  PostgreSQL Replica  │
                │  (Read)              │
                └──────────────────────┘
```

### CI/CD Pipeline

**Development Workflow:**
```
Code Commit (Git) → GitHub/GitLab
      ↓
Run Tests (pytest, ESLint)
      ↓
Build Docker Images (if using containers)
      ↓
Deploy to Staging Environment
      ↓
Manual QA / Testing
      ↓
Deploy to Production
      ↓
Health Checks
```

**Tools:**
- **GitHub Actions** or **GitLab CI**
- **Docker** (future)
- **Ansible** or **Fabric**: Deployment automation

---

## Development to Production Evolution

### Phase 1: MVP (Monorepo, Single Server)
- All services in one repository
- Deployed on single VPS
- Shared database (separate schemas per service)
- Good for rapid development

### Phase 2: Growth (Separate Repos, Multi-Server)
- Split services into separate repositories
- Database server separation
- Add read replicas
- CDN for static assets

### Phase 3: Scale (Cloud, Kubernetes)
- Migrate to AWS/GCP/Azure
- Kubernetes for orchestration
- Managed databases (RDS, Cloud SQL)
- Auto-scaling
- Multi-region deployment

---

## Technology Stack Summary by Layer

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React, TypeScript, Next.js |
| **API Gateway** | Nginx, Django Middleware |
| **Backend Services** | Django, Django REST Framework, Graphene-Django |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Vector DB** | Pinecone |
| **Background Jobs** | Celery, Celery Beat |
| **Message Broker** | Redis (Celery) |
| **Real-time** | Django Channels, Redis Channels Layer |
| **AI/ML** | LangChain, OpenAI, Anthropic, Custom Models |
| **Authentication** | Auth0, JWT |
| **Web Scraping** | Scrapy, Selenium, BeautifulSoup |
| **Monitoring** | Sentry, Prometheus, Grafana |
| **Logging** | ELK Stack (future) |

---

## Next Steps for Architecture Implementation

### Immediate (Week 1-2):
1. Set up development environment
2. Create base Django project structure
3. Define API contracts (OpenAPI specs)
4. Set up PostgreSQL and Redis locally
5. Implement User Service (authentication)

### Short-term (Week 3-6):
1. Implement Assessment Service core logic
2. Implement Roadmap Service core logic
3. Set up Celery for background processing
4. Create initial database schemas
5. Build API Gateway routing

### Medium-term (Month 2-3):
1. Complete all microservices
2. Implement GraphQL layer
3. Set up WebSocket infrastructure
4. Deploy to staging environment
5. Load testing and optimization

---

*Last Updated: November 2025*  
*Status: Architecture Design Phase - Subject to refinement during implementation*
