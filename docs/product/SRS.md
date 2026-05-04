# Software Requirements Specification (SRS)
## Sha8alny – AI-Powered Career Development Platform

> **Implementation note (May 2026):** This SRS was written when the project
> assumed OpenAI/Anthropic APIs. The implementation now uses deterministic Django
> AI workflows with hosted Gemini as the default demo provider and local Gemma via
> Ollama as the fallback — see [ADR-002](ADR-002-HOSTED-DEMO-AI-RUNTIME.md).
> All functional requirements remain the same; only the provider contract has changed.

---

# Table of Contents
1. Introduction  
   1.1 Purpose  
   1.2 Scope  
   1.3 Definitions, Acronyms, and Abbreviations  
   1.4 References  
   1.5 Overview  

2. Overall Description  
   2.1 Product Perspective  
   2.2 Product Functions  
   2.3 User Characteristics  
   2.4 Constraints  
   2.5 Assumptions and Dependencies  

3. Specific Requirements  
   3.1 Functional Requirements  
   3.2 External Interface Requirements  
   3.3 Performance Requirements  
   3.4 Design Constraints  
   3.5 Software System Attributes  
   3.6 Other Requirements  

4. Appendices

---

# 1. Introduction

## 1.1 Purpose
This Software Requirements Specification (SRS) document provides a complete description of the functional and non-functional requirements for the **Sha8alny** platform.  
This document is intended for:

- Development team  
- Project supervisors and academic evaluators  
- Quality assurance engineers  
- Future maintenance teams  

The SRS defines what the software will accomplish and serves as the basis for design, implementation, and validation.

---

## 1.2 Scope

### **Product Name:**  
Sha8alny

### **Product Description**  
Sha8alny is an **AI-powered career development platform** designed to assist individuals in navigating career advancement. It solves the problem of fragmented career resources and lack of personalized guidance by providing integrated:

- AI skill assessment  
- Learning path generation  
- Career advisory assistance  
- Job market insights  

### **Primary Objectives**
1. **Personalized Career Assessment**  
   AI-driven evaluation of user skills aligned with career goals.

2. **Intelligent Roadmap Generation**  
   Tailored step-by-step learning paths based on assessment data.

3. **AI Career Advisory**  
   Conversational, context-aware guidance using RAG (Retrieval-Augmented Generation).

4. **Job Market Intelligence**  
   Aggregated job listings with direct access to external application portals.

### **Major System Functions**
- User authentication and profile management  
- AI-powered skill assessment  
- Personalized learning roadmap generation  
- Natural language career advisory chatbot  
- Job scraping and job listing presentation  
- User progress tracking and analytics  

### **Benefits**
- Reduces time to identify relevant steps  
- Provides unbiased skill assessment  
- Combines career resources into one platform  
- Scales personalized guidance without human counselors  

### **Scope Boundaries**
The MVP focuses on:

- Assessment  
- Roadmap generation  
- Advisory  
- Job market data for Egypt  

The MVP **does NOT include**:

- Creating proprietary courses  
- Mobile apps  
- Direct job application processing  

---

## 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| **AI** | Artificial Intelligence |
| **API** | Application Programming Interface |
| **Assessment** | AI-generated evaluation of user skills |
| **Auth0** | Third-party authentication provider |
| **Embedding** | Vector representation of text |
| **JWT** | JSON Web Token |
| **LLM** | Large Language Model |
| **MVP** | Minimum Viable Product |
| **RAG** | Retrieval-Augmented Generation |
| **Roadmap** | Structured learning path |
| **Vector DB** | Database for vector similarity search |
| **Web Scraping** | Automated extraction of website data |

---

## 1.4 Overview
The rest of the SRS includes:

- **Section 2 — Overall Description:** System context, user characteristics, constraints  
- **Section 3 — Specific Requirements:** Functional + non-functional requirements  
- **Section 4 — Appendices:** Diagrams, glossary  

---

## 2. Overall Description

### 2.1 Product Perspective
Sha8alny is a standalone, web-based platform integrated with external services.

#### **External Services**
- **Auth0** – Authentication  
- **LLM APIs** (OpenAI GPT-4, Claude) – AI processing  
- **Vector Database** – Semantic search for RAG  
- **Job Market Data** – Wuzzuf, Bayt scraping  

#### **User Interactions**
- Web browser  
- REST API  
- WebSockets for real-time functionality  

---

### 2.1.1 System Context

The system interacts with:

- Users  
- Auth0  
- LLM APIs  
- Vector database services  
- Job boards  

---

### 2.1.2 System Architecture Overview
Sha8alny follows a microservices architecture:

1. **Frontend Layer** – React SPA  
2. **API Gateway** – Request routing, authentication  
3. **Service Layer** – Separate microservices  
4. **Data Layer** – PostgreSQL + Vector DB  
5. **Integration Layer** – External APIs  

---

### 2.1.3 System Interfaces

#### **User Interface**
- Responsive web app (Chrome, Firefox, Safari, Edge)

#### **Hardware Interfaces**
- None (web-based only)

#### **Software Interfaces**
- Django REST Framework  
- React  
- PostgreSQL  
- Redis  
- Celery  

#### **Communication Interfaces**
- HTTPS  
- WebSockets  
- REST APIs  
### 2.2 Product Functions

Sha8alny provides the following high-level capabilities:

#### **1. User Account & Profile Management**
- Sign up / login (Auth0)
- Edit profile info
- Set career goals
- Update skill list
- Track learning progress

#### **2. AI Skill Assessment**
- Analyze user-provided information (CV text, goals, skills)
- Detect missing skills
- Benchmark user’s profile against target roles
- Provide assessment summary

#### **3. Roadmap (Learning Path) Generation**
- Generate career-aligned roadmaps
- Multi-phase breakdown:
  - Foundations
  - Intermediate
  - Advanced
- Identify resources:
  - Courses
  - Books
  - Articles
  - Tools
- Sync AI-generated phases to database
- Track roadmap completion

#### **4. AI Career Advisory (Chatbot)**
- General career questions
- Roadmap-related advice
- Interpretation of job listings
- Personalized recommendations using RAG

#### **5. Job Market Insights**
- Scrape job postings from Egyptian job boards
- Normalize job posting data
- Provide requirements & responsibilities
- Link to the official job page

#### **6. Analytics**
- Track:
  - Completed courses
  - Skill improvements
  - Time spent
- Display dashboards

---

### 2.3 User Characteristics

Sha8alny supports three main user types:

#### **1. Students**
- May have limited experience
- Learning new skills
- Seeking beginner-friendly guidance

#### **2. Job Seekers**
- Transitioning careers
- Need practical and fast learning paths
- Require job readiness help

#### **3. Professionals**
- Looking to upskill or specialize
- Require structured roadmaps and job alignment

#### **User Assumptions**
- Basic computer literacy
- Access to the Internet
- Understanding of English (main content language)

---

### 2.4 Constraints

| Constraint Type | Description |
|----------------|-------------|
| **Technical** | Limited compute resources; NLP models are external APIs |
| **Security** | All data must be encrypted in transit (HTTPS) |
| **Legal** | Job posting content must follow scraping regulations |
| **Performance** | API responses should be < 2s for non-AI endpoints |
| **Scalability** | Must support future mobile app integration |

---

### 2.5 Assumptions and Dependencies

#### **Assumptions**
- Users provide accurate data during skill assessment
- External APIs (Auth0, LLM provider) are operational
- Job websites allow scraping under fair-use rules
- Internet availability is stable

#### **Dependencies**
- Auth0 for authentication
- OpenAI/Anthropic for text generation
- PostgreSQL database availability
- Vector database for semantic search
- External job board structures may change over time

# 3. Specific Requirements

## 3.1 Functional Requirements

This section details all functional requirements organized by service.

---

# 3.1.1 User Service Requirements

### **FR-1: User Registration**
- The system shall allow users to register using Auth0.
- The system shall store the user’s `auth0_id`, email, and minimal profile data.

### **FR-2: User Login**
- The system shall authenticate users using Auth0 and return a JWT access token.

### **FR-3: Profile Management**
- Users shall be able to:
  - Edit personal information
  - Set career goals
  - Upload/pre-fill skills
  - Add experience summary

### **FR-4: User Preferences**
- The system shall store:
  - Preferred learning format
  - Target job role
  - Interests
  - Language preference

### **FR-5: Skill Tracking**
- The system shall allow adding and modifying user skills.
- The system shall update skill levels after roadmap progress.

---

# 3.1.2 Assessment Service Requirements

### **FR-6: Generate Skill Assessment**
- The system shall accept user input:
  - CV text
  - Career goals
  - Skills
- The system shall process the information via LLM.
- The system shall generate:
  - Current skill levels
  - Missing skills
  - Recommended improvements

### **FR-7: Assessment Versioning**
- The system shall store each assessment result with a timestamp.
- Users can view past assessments.

### **FR-8: AI Processing**
- The system shall send structured prompts to LLM API.
- The system shall parse the response into:
  - Skills
  - Levels
  - Notes
  - Recommendations

---

# 3.1.3 Roadmap Service Requirements

### **FR-9: Roadmap Generation**
- The system shall generate a multi-phase learning roadmap using AI.
- Phases include:
  - Foundations
  - Intermediate
  - Advanced

### **FR-10: Roadmap Structure**
A roadmap shall contain:

| Entity | Description |
|-------|-------------|
| **Roadmap** | High-level container |
| **Phase** | Group of milestones |
| **Milestone** | Specific tasks/skills |
| **Course** | External learning resources |

### **FR-11: Course Association**
- The system shall map skills to external courses using:
  - Skill keywords
  - Embeddings similarity search
  - Manual admin curation

### **FR-12: Roadmap Versioning**
- Each AI-generated roadmap shall be stored.
- Users can regenerate roadmaps.

### **FR-13: Progress Tracking**
- The system shall track completion:
  - Completed milestones
  - Completed phases
  - Started roadmap
  - Completed roadmap

---

# 3.1.4 Advisory Service (Chatbot)

### **FR-14: Chat Handling**
- The system shall handle user queries through an AI chatbot.

### **FR-15: Context Awareness**
- The advisory chatbot shall retrieve:
  - User profile
  - Latest roadmap
  - Assessment data
- Using the RAG pipeline.

### **FR-16: Response Generation**
- The system shall generate advisory responses using LLM.

### **FR-17: Conversation History**
- Store user messages and AI responses.

---

# 3.1.5 Job Market Service Requirements

### **FR-18: Job Scraping**
- The system shall scrape job boards (e.g., Wuzzuf, Indeed, Bayt).

### **FR-19: Job Normalization**
- All jobs shall be stored with unified fields:
  - Title
  - Company
  - Location
  - Requirements
  - Responsibilities
  - Apply URL

### **FR-20: Job Search**
- The system shall allow filtering by:
  - Role
  - Level
  - Keywords
  - Location

### **FR-21: Job Insights**
- The system shall provide:
  - Skills required for each role
  - Missing skills based on user profile

---

# 3.1.6 Analytics Service Requirements

### **FR-22: Dashboard Generation**
- The system shall show user progress metrics.

### **FR-23: Skill Growth Tracking**
- The system shall compare assessment results over time.

### **FR-24: Engagement Tracking**
- The system shall track:
  - Login frequency
  - Roadmap interactions
  - Chatbot usage

# 3.2 External Interface Requirements

## 3.2.1 User Interfaces (UI)

### **UI-1: Web Application**
- Responsive design (desktop, tablet, mobile)
- Clean dashboard showing:
  - Assessment results
  - Roadmap progress
  - Job recommendations
  - Chatbot access

### **UI-2: Navigation**
- Sidebar or top navigation containing:
  - Home
  - Assessments
  - Roadmap
  - Jobs
  - Chatbot
  - Profile

### **UI-3: Accessibility**
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Sufficient contrast ratio

### **UI-4: Feedback & Loading States**
- Skeleton loading for AI
- Toast notifications
- Retry options

---

## 3.2.2 Hardware Interfaces
- None (web-based platform)

---

## 3.2.3 Software Interfaces

### **SI-1: Authentication (Auth0)**
- OAuth2 / OpenID Connect
- Redirect URLs for login/logout

### **SI-2: Database (PostgreSQL)**
- Stores relational data:
  - Users
  - Skills
  - Roadmaps
  - Jobs

### **SI-3: Vector Database**
- Stores embeddings for:
  - Skills
  - Career knowledge base
  - Course descriptions

### **SI-4: LLM API (OpenAI, Anthropic)**
- Used for:
  - Skill assessment
  - Roadmap generation
  - Chat advisory
  - Text embedding generation

### **SI-5: Job Websites**
- External job boards for scraping
- Must handle:
  - HTML changes
  - Rate limiting

---

## 3.2.4 Communication Interfaces

### **CI-1: REST API**
- JSON-based request/response
- Endpoints follow standard conventions:
  - `GET /api/...`
  - `POST /api/...`

### **CI-2: HTTPS**
- Required for secure communication

### **CI-3: WebSockets**
- Used for:
  - Real-time chatbot responses
  - Live progress updates

### **CI-4: Email Integration**
- Used for:
  - Notifications
  - Account verification (future)

---

# 3.3 Performance Requirements

### **PR-1: Response Time**
- Non-AI API requests: **≤ 2 seconds**
- AI requests (LLM): **≤ 7 seconds** average

### **PR-2: Concurrency**
- System must support **300+ concurrent users** (MVP)

### **PR-3: Throughput**
- API Gateway should handle **up to 50 requests/sec**

### **PR-4: Data Processing**
- Roadmap generation should complete in **< 10 seconds**
- Skill assessment should complete in **< 12 seconds**

### **PR-5: Job Scraping**
- Scraping tasks should run:
  - Every 12 hours
  - Parallelized
  - With retry logic

---

# 3.4 Design Constraints

### **DC-1: Architecture**
- Microservices architecture (5 major services)
- Dockerized deployment

### **DC-2: Language & Framework**
- Backend: Python (Django Rest Framework)
- Frontend: React.js
- Database: PostgreSQL

### **DC-3: Security**
- Must follow OWASP Top 10 guidelines

### **DC-4: API Design**
- Follows REST principles
- Uses JWT authentication

### **DC-5: Cloud Infrastructure**
- Deployable on:
  - AWS
  - Render
  - Railway
  - Docker Swarm
  - Kubernetes (future)

---

# 3.5 Software System Attributes

## 3.5.1 Reliability
- System should maintain **99% uptime**
- Automatic retries for failed tasks
- Graceful error handling

## 3.5.2 Availability
- Critical services must be available during peak hours
- Failover for:
  - Database
  - LLM API (fallback provider)

## 3.5.3 Security
- Passwords are **never** stored (Auth0-only)
- All sensitive data encrypted (AES-256 for storage)
- HTTPS mandatory
- Role-based access control (future)

## 3.5.4 Maintainability
- Modular codebase
- Clear naming conventions
- Comprehensive documentation

## 3.5.5 Portability
- Backend containerized via Docker
- React frontend portable to mobile wrapper (React Native)

# 3.6 Other Requirements

## 3.6.1 Logging & Monitoring
- The system shall log:
  - All API calls
  - Errors and exceptions
  - Scraper failures
  - Chatbot conversations
- Logs shall be stored with timestamps.
- Monitoring dashboard required (Grafana or similar).

## 3.6.2 Backup Requirements
- Daily database backups
- Weekly vector DB backups
- Backup retention: 30 days

## 3.6.3 Localization
- Primary language: English
- Arabic planned for future release

## 3.6.4 Compliance
- GDPR-like privacy rules for user data
- Clear data deletion policy

---

# 4. Appendices

## Appendix A — Domain Model Diagram (Text Description)
User
├── Profile
├── Skills
├── Assessments
│ └── AssessmentResult
├── Roadmap
│ ├── RoadmapPhase
│ │ └── RoadmapMilestone
│ │ └── RoadmapCourse
└── Job Insights


---

## Appendix B — API Endpoint Summary (MVP)

### **User Service**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login via Auth0 |
| GET | `/users/me` | Get current user profile |
| PUT | `/users/me` | Update profile |
| GET | `/users/skills` | List user skills |
| POST | `/users/skills` | Add skill |

---

### **Assessment Service**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/assessment/` | Generate assessment |
| GET | `/assessment/latest` | Latest assessment |
| GET | `/assessment/history` | All assessments |

---

### **Roadmap Service**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/roadmap/` | Generate roadmap |
| GET | `/roadmap/` | Get current roadmap |
| PUT | `/roadmap/progress` | Update progress |

---

### **Advisory Service**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/advisory/chat` | Chat with AI |
| GET | `/advisory/history` | View conversation logs |

---

### **Job Service**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs/search` | Job search |
| GET | `/jobs/<id>` | Job details |

---

## Appendix C — Non-Functional Requirements Summary

### **Security**
- JWT-based access control
- HTTPS everywhere
- No password storage

### **Scalability**
- Horizontal scalability using containers
- Modular microservices

### **Performance**
- API response targets defined in Section 3.3

### **Usability**
- Minimalistic UI
- Page load < 3 seconds

---

## Appendix D — Glossary

| Term | Definition |
|------|------------|
| **Roadmap** | Structured learning path containing phases and milestones |
| **Milestone** | A specific actionable learning goal |
| **Phase** | A group of milestones in a roadmap |
| **Embedding** | Vector representation used for semantic search |
| **RAG** | Retrieval-Augmented Generation |
| **LLM** | Large Language Model |
| **Dashboard** | Page displaying analytics data |

---

# END OF DOCUMENT
