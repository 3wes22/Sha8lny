# Sha8lny - شغّلني
## AI-Powered Career Empowerment Platform
### Nile University Graduation Project 2025 | ITCS Department

---

# 📋 Presentation Guide

| Section | Presenter | Duration | Importance | Notes |
|---------|-----------|----------|------------|-------|
| 1. Introduction & Problem | Person 1 | 3-4 min | 🟡 Moderate | Easy, scripted - Good for less-experienced |
| 2. System Architecture | Person 2 | 5-6 min | 🔴 Very Important | Must know system deeply |
| 3. Backend Development | Person 3 | 5-6 min | 🔴 Very Important | Technical, needs expertise |
| 4. Frontend Development | Person 4 | 4-5 min | 🟠 Important | Demo focused |
| 5. AI/RAG System | Person 5 | 5-6 min | 🔴 Very Important | Core innovation |
| 6. Demo & Conclusion | Person 6 | 3-4 min | 🟡 Moderate | Easy wrap-up - Good for less-experienced |

---

# SECTION 1: Introduction & Problem Statement
## 🟡 Moderate Importance | 3-4 minutes

---

## Slide 1.1: The Career Crisis

### 🇪🇬 Egypt's Youth Employment Challenge

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     📊 27% Youth Unemployment Rate in Egypt                   ║
║                                                               ║
║     🎓 700,000+ Graduates Enter Job Market Yearly             ║
║                                                               ║
║     ❌ 60% of Graduates Work in Unrelated Fields              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

> **The Gap**: Students don't know what skills they need, and companies can't find qualified candidates.

---

## Slide 1.2: The Problem We're Solving

### ❌ Current Reality for Students:

| Problem | Impact |
|---------|--------|
| 🤷 No clear career direction | Wasted years studying wrong topics |
| 📚 Outdated curriculum | Skills don't match job market |
| 🔍 Overwhelming online resources | Don't know where to start |
| 💼 No practical guidance | Generic advice doesn't help |
| 🌐 Disconnected from local market | International content, Egyptian needs |

### ✅ What Students Need:

- Personalized career assessment
- Skills-to-job mapping
- Egyptian market insights
- AI-guided learning paths

---

## Slide 1.3: Introducing Sha8lny

### 🚀 The Solution: AI-Powered Career Guidance

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    شغّلني | Sha8lny                         │
│                                                             │
│        "Your AI Career Companion for the Egyptian Market"   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Value Proposition:

> **From Confused Graduate → Employed Professional**
> 
> Using AI + Egyptian Market Data + Personalized Learning

---

## Slide 1.4: Key Features Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   🧠 AI Career Assessment          📈 Personalized Roadmaps                 │
│   └─ Evaluate skills & gaps        └─ Step-by-step learning paths          │
│                                                                              │
│   💼 Egyptian Job Integration      🤖 AI Career Advisor                     │
│   └─ Real jobs from Wuzzuf/Bayt    └─ 24/7 career chatbot                   │
│                                                                              │
│   📚 Smart Course Matching         📊 Market Insights                       │
│   └─ Udemy, Coursera, YouTube      └─ Trending skills & salaries            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Slide 1.5: Project Scope — Academic Deliverables Matrix

### First Half Milestones (Completed)

| Deliverable Category | Academic Output | Status |
|---------------------|-----------------|--------|
| Requirements Engineering | Software Requirements Specification (SRS) | ✅ |
| Architectural Methodology | System Design Documents (ERD, HLD) | ✅ |
| Backend Implementation | Django RESTful API (10 Service Modules) | ✅ |
| Frontend Development | React TypeScript UI (15 Production Pages) | ✅ |
| AI Infrastructure | RAG Pipeline + ChromaDB Integration | ✅ |

### Academic Deliverables (Second Half)

| Phase | Deliverable | Evaluation Criteria |
|-------|-------------|--------------------|
| Integration | Frontend-Backend API Integration | Functional completeness |
| Authentication | Auth0 OAuth 2.0 Implementation | Security compliance |
| Deployment | Docker + AWS Production Environment | Scalability metrics |
| Validation | User Acceptance Testing (UAT) | Usability scoring |

---

# SECTION 2: System Architecture
## 🔴 Very Important | 5-6 minutes

---

## Slide 2.1: High-Level Architecture

### Modular Monolithic Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui       │  │
│  │  • 15 Production Pages  • Responsive Design  • Modern UI/UX   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ REST API / HTTPS
┌─────────────────────────────────────────────────────────────────────┐
│                    DJANGO MONOLITH (10 Modules)                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Django 5.x + Django REST Framework + JWT Authentication      │  │
│  │                                                               │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐        │  │
│  │  │  Users  │ │Assessment│ │ Roadmaps │ │  Advisory  │        │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────┘        │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐        │  │
│  │  │ Courses │ │   Jobs   │ │ Progress │ │Career Tools│        │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────┘        │  │
│  │  ┌─────────────┐  ┌─────────────┐                             │  │
│  │  │Notifications│  │    Core     │                             │  │
│  │  └─────────────┘  └─────────────┘                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA & AI LAYER                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ PostgreSQL │  │   Redis    │  │  ChromaDB  │  │  LM Studio │    │
│  │ (Primary)  │  │(Task Queue)│  │ (Vectors)  │  │   (LLM)    │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Slide 2.2: Architectural Methodology — Modular Monolith Selection

### Heuristic Evaluation: Monolith vs. Microservices

| Criterion | Modular Monolith | Microservices | Decision Factor |
|-----------|------------------|---------------|----------------|
| **Development Velocity** | ✅ Single codebase iteration | ❌ Multi-repo coordination | MVP timeline (16 weeks) |
| **ACID Compliance** | ✅ Native PostgreSQL transactions | ❌ Distributed saga patterns | Data integrity critical |
| **Operational Overhead** | ✅ Single deployment artifact | ❌ Kubernetes orchestration | Team size (N<6) |
| **Latency Profile** | ✅ In-process function calls | ❌ Inter-service HTTP overhead | Real-time UX |
| **Infrastructure Cost** | ✅ Single compute instance | ❌ Multiple service containers | Academic budget |

### Academic Justification

> **Conway's Law Alignment**: Our team structure (4-6 developers) maps directly to a unified codebase, avoiding the coordination overhead inherent in distributed systems.

> **Future Extensibility**: Module boundaries are designed for potential service extraction post-MVP, following the Strangler Fig pattern.

---

## Slide 2.3: Technology Stack

### Complete Tech Stack:

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, Vite, TypeScript, TailwindCSS, shadcn/ui |
| **Backend** | Django 5.x, Django REST Framework, JWT Auth |
| **Database** | PostgreSQL (primary), Redis (cache) |
| **AI/ML** | LM Studio, ChromaDB, Sentence Transformers |
| **Data Sources** | O*NET, roadmap.sh, Wuzzuf, Bayt |
| **DevOps** | Docker, Git, GitHub |

---

## Slide 2.4: Data Flow - Assessment & Roadmap

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  ASSESSMENT TO ROADMAP FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

   👤 User                      🖥️ Frontend                    🔧 Backend
     │                              │                              │
     │  1. Start Assessment         │                              │
     ├─────────────────────────────>│                              │
     │                              │  POST /assessments/start     │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │  2. Answer Questions         │                              │
     ├─────────────────────────────>│                              │
     │                              │  POST /assessments/submit    │
     │                              ├─────────────────────────────>│
     │                              │                              ↓
     │                              │                     ┌────────────────┐
     │                              │                     │  Celery Task   │
     │                              │                     │  (Background)  │
     │                              │                     └────────┬───────┘
     │                              │                              │
     │                              │                              ↓
     │                              │                     ┌────────────────┐
     │                              │                     │   LLM + RAG    │
     │                              │                     │  Analysis      │
     │                              │                     └────────┬───────┘
     │                              │                              │
     │  3. Get Personalized         │                              │
     │     Roadmap                  │    Roadmap Generated         │
     │<─────────────────────────────│<─────────────────────────────│
```

---

## Slide 2.5: Entity Relationship Diagram

### Core Database Entities:

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    User     │────<│   Assessment    │────>│   Roadmap   │
│             │     │                 │     │             │
│ • name      │     │ • questions     │     │ • phases    │
│ • email     │     │ • responses     │     │ • milestones│
│ • skills    │     │ • results       │     │ • courses   │
└──────┬──────┘     └─────────────────┘     └──────┬──────┘
       │                                           │
       │            ┌─────────────────┐            │
       └───────────>│    Progress     │<───────────┘
                    │                 │
                    │ • completion %  │
                    │ • skills gained │
                    │ • time spent    │
                    └─────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ↓                    ↓                    ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Courses   │     │    Jobs     │     │ Job Application │
│             │     │             │     │                 │
│ • Udemy     │     │ • Wuzzuf    │     │ • status        │
│ • Coursera  │     │ • Bayt      │     │ • AI match %    │
└─────────────┘     └─────────────┘     └─────────────────┘
```

---

# SECTION 3: Backend Development
## 🔴 Very Important | 5-6 minutes

---

## Slide 3.1: RESTful API Architecture

### Endpoint Design Pattern

| Module | Endpoint Pattern | Authentication | Rate Limit |
|--------|------------------|----------------|------------|
| **Users** | `/api/v1/users/` | JWT (Auth0-ready) | 100/min |
| **Assessments** | `/api/v1/assessments/` | JWT Required | 10/min |
| **Roadmaps** | `/api/v1/roadmaps/` | JWT Required | 50/min |
| **Advisory** | `/api/v1/advisory/chat/` | JWT + Throttling | 20/min |
| **Jobs** | `/api/v1/jobs/` | Public + JWT Enhanced | 200/min |
| **Courses** | `/api/v1/courses/` | Public | 200/min |

### JWT Authentication Flow

```
1. User authenticates → Access Token (15 min) + Refresh Token (7 days)
2. Access token in Authorization header: Bearer <token>
3. Automatic token refresh via interceptor
4. Role-based permission decorators: @permission_classes([IsAuthenticated])
```

---

## Slide 3.2: Asynchronous Task Processing Architecture

### Celery + Redis Task Queue

```
┌────────────────────────────────────────────────────────────────┐
│                BACKGROUND TASK PROCESSING                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Django API ──→ Redis Broker ──→ Celery Worker Pool            │
│   (returns      (message       (executes AI inference)         │
│    task_id)      queue)                                        │
│                                                                │
│  Task Types:                                                   │
│  ├── assessment_analysis.task  (LLM skill evaluation)          │
│  ├── roadmap_generation.task   (RAG-enhanced planning)         │
│  ├── job_scraping.task         (Wuzzuf/Bayt ingestion)         │
│  └── notification_dispatch.task(Email/Push delivery)           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Task Queue Benefits
- Non-blocking API responses for AI inference
- Horizontal scalability via worker pool
- Retry mechanism with exponential backoff

---

## Slide 3.3: PostgreSQL Database Engineering

### Optimization Strategies

| Design Pattern | Implementation | Rationale |
|----------------|----------------|----------|
| **UUID Primary Keys** | `uuid.uuid4()` on all models | Distributed-ready, no collision |
| **JSONB Metadata** | `Assessment.responses`, `Roadmap.ai_metadata` | Schema flexibility for AI data |
| **Soft Delete** | `BaseModel.is_deleted` flag | Audit trail preservation |
| **Strategic Indexing** | 40+ custom indexes on query paths | O(log n) lookups |
| **Composite Constraints** | `unique_together`, `UniqueConstraint` | Data integrity |

### JSONB Usage Patterns

```python
# Flexible AI metadata storage
Assessment.questions    # Dynamic question structures
Roadmap.ai_metadata     # LLM generation parameters  
Message.context_used    # RAG retrieval snapshots
Job.extra_data          # Platform-specific fields
```

---

# SECTION 4: Frontend Development
## 🟠 Important | 4-5 minutes

---

## Slide 4.1: Frontend Page Architecture (15 Production Pages)

### Functional Cluster Organization

| Cluster | Pages | User Journey |
|---------|-------|-------------|
| **User Assessment** | Assessment, AssessmentSession, AssessmentResults | Skill evaluation → AI analysis → Results display |
| **Job Discovery** | Jobs, SavedJobs | Search → Filter → Bookmark → Apply |
| **AI Advisory** | Advisor | RAG-powered career chatbot |
| **User Management** | Login, Register, Profile, Settings | Auth → Preferences |
| **Learning Path** | Roadmap | Personalized roadmap visualization |
| **Core Navigation** | Dashboard, Index, NotFound | Entry points & error handling |

---

# SECTION 5: AI/RAG System
## 🔴 Very Important | 5-6 minutes

---

## Slide 5.1: RAG Architecture Overview

### Retrieval-Augmented Generation (RAG):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          RAG PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐                                                       │
│   │ User Query   │  "What skills do I need to become a backend dev?"    │
│   └──────┬───────┘                                                       │
│          │                                                               │
│          ↓                                                               │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                     EMBEDDING MODEL                               │  │
│   │              all-MiniLM-L6-v2 (384 dimensions)                    │  │
│   └──────────────────────────┬───────────────────────────────────────┘  │
│                              ↓                                           │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                  VECTOR SIMILARITY SEARCH                         │  │
│   │                       ChromaDB                                    │  │
│   │                                                                   │  │
│   │  ┌─────────────────┐    ┌─────────────────┐                      │  │
│   │  │   roadmap.sh    │    │    O*NET DB     │                      │  │
│   │  │   (Learning)    │    │    (Jobs)       │                      │  │
│   │  └─────────────────┘    └─────────────────┘                      │  │
│   └──────────────────────────┬───────────────────────────────────────┘  │
│                              ↓                                           │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                   TOP-K RELEVANT CHUNKS                           │  │
│   │           "Node.js basics...", "API design...", etc.              │  │
│   └──────────────────────────┬───────────────────────────────────────┘  │
│                              ↓                                           │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                     LLM (LM Studio)                               │  │
│   │              Gemma-2 / Qwen / Llama-3.2                           │  │
│   │                                                                   │  │
│   │  System: "You are Sha8lny, a career advisor..."                  │  │
│   │  Context: [Retrieved chunks]                                      │  │
│   │  Query: "What skills do I need..."                               │  │
│   └──────────────────────────┬───────────────────────────────────────┘  │
│                              ↓                                           │
│   ┌──────────────┐                                                       │
│   │ AI Response  │  "To become a backend developer, you need..."        │
│   └──────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Slide 5.2: Knowledge Base Engineering

### Data Source Integration

| Source | Content Type | Processing Method |
|--------|-------------|-------------------|
| **roadmap.sh** | 30+ career learning paths (Markdown) | Regex cleaning → chunking |
| **O*NET Database** | US Labor occupational data (TSV) | Row-level document extraction |
| **Key O*NET Files** | Skills, Knowledge, Abilities, Tasks | Structured field indexing |

### ChromaDB Vector Store Specifications

| Parameter | Value | Configuration Source |
|-----------|-------|---------------------|
| **Collection Name** | `career_knowledge` | build_vector_db.py |
| **Chunk Size** | 500 characters | CHUNK_SIZE constant |
| **Chunk Overlap** | 50 characters | CHUNK_OVERLAP constant |
| **Embedding Model** | all-MiniLM-L6-v2 | Sentence Transformers |
| **Embedding Dimensions** | 384 | Model specification |
| **Batch Size** | 100 documents | Memory optimization |
| **Query Latency** | <100ms | Measured performance |

---

## Slide 5.3: Smart Source Selection

### Intelligent Query Routing:

```python
# Detect question type → choose optimal source
learning_keywords = ['become', 'learn', 'roadmap', 'path', 'start']
job_keywords = ['work activities', 'job tasks', 'occupation', 'duties']

if any(kw in question_lower for kw in learning_keywords):
    source_filter = {"source": "roadmap.sh"}  # Learning paths
elif any(kw in question_lower for kw in job_keywords):
    source_filter = {"source": "onet"}  # Job data
else:
    source_filter = None  # Search all
```

### Benefits:
- ⚡ Faster queries (smaller search space)
- 🎯 More relevant results
- 📈 Better answer quality

---

## Slide 5.4: Anti-Hallucination Prompt Engineering

### System Prompt Design

```python
system_prompt = """You are Sha8lny, a helpful career advisor.

RULES:
1. USE the context below to answer the question
2. If context contains relevant information, provide helpful answer
3. Only say "I don't know" if context is completely unrelated
4. For off-topic questions, politely redirect to career topics
5. Don't invent specific numbers or statistics not in context
"""
```

### LLM Configuration (from `query_with_lmstudio.py`)

| Parameter | Value | Rationale |
|-----------|-------|----------|
| **Temperature** | 0.3 | Balanced: factual but natural responses |
| **Max Tokens** | 400 | Sufficient for detailed career guidance |
| **TOP_K Retrieval** | 3 | Quality over quantity (focused context) |
| **Timeout** | 30 seconds | Prevent hanging requests |

---

## Slide 5.5: LM Studio Local Inference

### Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                 LM STUDIO CONFIGURATION                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📦 Tested Models:                                          │
│     • Gemma-2-2b-it                                         │
│     • Qwen2.5-1.5B-Instruct                                 │
│                                                             │
│  ⚙️ Runtime Parameters:                                     │
│     • Context Length: 4096 tokens                           │
│     • Temperature: 0.3                                       │
│     • Max Tokens: 400                                        │
│     • API Endpoint: localhost:1234/v1/chat/completions       │
│                                                             │
│  ✅ Development Advantages:                                  │
│     • Zero API costs during development                     │
│     • Full data privacy (local inference)                   │
│     • Rapid prompt iteration                                │
│     • Offline capability                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# SECTION 6: Demo & Conclusion
## 🟡 Moderate Importance | 3-4 minutes

---

## Slide 6.1: Live Demonstration Flow

### High-Impact Feature Prioritization

| Priority | Feature | Demonstration Focus | Duration |
|----------|---------|--------------------|---------|
| 1️⃣ | **AI Career Advisor** | RAG-powered Q&A, context awareness | 90 sec |
| 2️⃣ | **Skill Assessment** | AI-generated questions, real-time scoring | 60 sec |
| 3️⃣ | **Personalized Roadmap** | Generated learning path visualization | 45 sec |
| 4️⃣ | **Job Matching** | Skills-based recommendations, match % | 30 sec |
| 5️⃣ | **User Dashboard** | Progress tracking, stats overview | 15 sec |

> **Backup Plan**: Pre-recorded video demonstration available if live demo encounters issues

---

## Slide 6.2: First Half Achievements

### Completed Deliverables

- ✅ **Architectural Design** — Modular Monolithic Architecture
- ✅ **Backend Implementation** — Django RESTful API (10 Modules)
- ✅ **Frontend Development** — React TypeScript (15 Pages)
- ✅ **Database Engineering** — PostgreSQL + JSONB (25+ Models)
- ✅ **RAG Pipeline** — ChromaDB + Sentence Transformers
- ✅ **AI Integration** — LM Studio Local Inference

### Key Metrics:
- **~15,000 lines** of backend code
- **~10,000 lines** of frontend code
- **60,000+** knowledge documents indexed
- **<100ms** RAG query latency

---

## Slide 6.3: Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| 📉 **LLM Hallucination** | Strong anti-hallucination prompts + low temperature |
| ⏱️ **Slow AI Responses** | Background processing with Celery |
| 📚 **Data Quality** | Multiple sources (O*NET, roadmap.sh) |
| 🔗 **Integration Complexity** | Service layer pattern for clean architecture |
| 💰 **API Costs** | Local LLM inference with LM Studio |

---

## Slide 6.4: Second Half Development Roadmap

### Phase 1: Integration (Weeks 1-2)
- Frontend-Backend API integration
- Real-time progress synchronization

### Phase 2: Authentication (Weeks 2-3)
- **Auth0 Universal Login** implementation
- Social providers (Google, LinkedIn)
- JWT refresh token rotation
- Role-based access control (RBAC)

### Phase 3: Job Scraping (Weeks 3-4)
- Wuzzuf API integration
- Bayt.com scraper implementation

### Phase 4: Deployment (Weeks 5-7)
- Docker multi-stage containerization
- AWS ECS Fargate orchestration
- RDS PostgreSQL + ElastiCache Redis
- CloudFront CDN + Route 53 DNS

### Phase 5: Validation (Weeks 7-8)
- User Acceptance Testing (UAT)
- API documentation (OpenAPI/Swagger)

---

## Slide 6.5: Conclusion

### Sha8lny Vision:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   "Empowering Egyptian students and graduates with              │
│    AI-driven career guidance, personalized learning paths,      │
│    and real-time job market insights"                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Takeaways:

1. 🎯 **Solving Real Problems**: 27% youth unemployment in Egypt
2. 🤖 **AI-Powered**: RAG + LLM for personalized guidance
3. 🏗️ **Solid Architecture**: Modular monolith, ready to scale
4. 📊 **Data-Driven**: O*NET + roadmap.sh + Egyptian market data
5. 🚀 **On Track**: First half milestones completed

---

## Slide 6.6: Thank You & Q&A

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                    شكراً لاستماعكم 🙏                             ║
║                                                                   ║
║                    Thank You for Listening!                       ║
║                                                                   ║
║                         Questions?                                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Team Sha8lny
**Nile University | ITCS Department | 2025**

---

# 📎 Appendix: Q&A Cheat Sheet

## Common Questions & Answers:

### Q: Why not use microservices?
> A: For an MVP, modular monolith provides faster development, simpler deployment, and ACID transactions. We can extract services later if needed.

### Q: How do you prevent AI hallucination?
> A: Temperature set to 0.3 for balanced responses, strict context-grounding prompts, and TOP_K=3 for focused retrieval.

### Q: Why local LLM instead of OpenAI?
> A: Cost savings during development, data privacy, and faster iteration. Production may use cloud APIs.

### Q: How accurate is the career matching?
> A: We use O*NET (US Labor Data) combined with Egyptian job market data for accurate skill-to-job mapping.

### Q: What makes this different from existing platforms?
> A: Egyptian market focus, AI personalization, integration of assessment→roadmap→jobs pipeline.

---

# 📊 Appendix: Technical Details

## Key Files Reference:

| File | Purpose |
|------|---------|
| `Backend/apps/advisory/` | AI chatbot implementation |
| `ai-models/src/rag/build_vector_db.py` | ChromaDB builder |
| `ai-models/src/rag/query_with_lmstudio.py` | RAG query engine |
| `docs/ARCHITECTURE.md` | Full system design |
| `docs/DATABASE_SCHEMA.md` | Complete DB schema |
| `docs/SRS.md` | Requirements spec |

---

*Created for Sha8lny Graduation Project - Nile University 2025*
