# SkillPath AI - System Architecture Design

> **Document Version:** 1.0
> **Last Updated:** November 4, 2025
> **Architecture Phase:** MVP Design

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Services](#core-services)
4. [Technology Stack](#technology-stack)
5. [Service Communication](#service-communication)
6. [External Dependencies](#external-dependencies)
7. [Security Architecture](#security-architecture)
8. [Scalability Strategy](#scalability-strategy)

---

## System Overview

### Architecture Style

**Modular Monolith** → Microservices evolution path

**Rationale:**
- **MVP Constraints:** $0 budget, small team, 2-month timeline
- **Modular Design:** Clear service boundaries enable future microservices migration
- **Simplicity:** Single deployment reduces operational complexity
- **Performance:** In-process communication, no network overhead
- **Cost:** One server instance, minimal infrastructure

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web App    │  │  Mobile App  │  │  Admin Panel │          │
│  │  (React.js)  │  │  (Future)    │  │  (React.js)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  API Gateway / Load Balancer (Nginx/Traefik)           │    │
│  │  - Rate Limiting                                        │    │
│  │  - Request Routing                                      │    │
│  │  - SSL Termination                                      │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER (Node.js)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CORE BACKEND SERVICES                       │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Auth       │  │  Assessment  │  │   Learning   │  │   │
│  │  │   Service    │  │   Service    │  │   Service    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │     Job      │  │     AI       │  │    User      │  │   │
│  │  │   Service    │  │  Integration │  │   Service    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐                    │   │
│  │  │Notification  │  │ Analytics    │                    │   │
│  │  │  Service     │  │  Service     │                    │   │
│  │  └──────────────┘  └──────────────┘                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │  File Store  │          │
│  │  (Primary DB)│  │   (Cache)    │  │  (S3/Local)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  OpenAI/     │  │  Job APIs    │  │  Email       │          │
│  │  Claude API  │  │  (LinkedIn,  │  │  Service     │          │
│  │              │  │   Wuzzuf)    │  │  (SMTP)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Services

### 1. Authentication Service

**Responsibilities:**
- User registration and login
- Password hashing (bcrypt)
- JWT token generation and validation
- Refresh token management
- Password reset flows
- Email verification

**Key Endpoints:**
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

**Database Tables:**
- `users` (id, email, password_hash, role, created_at)
- `refresh_tokens` (id, user_id, token, expires_at)
- `verification_tokens` (id, user_id, token, type, expires_at)

**Security Features:**
- Rate limiting on login attempts
- Account lockout after failed attempts
- Password strength validation
- Secure token storage

---

### 2. User Service

**Responsibilities:**
- User profile management
- User preferences (learner vs jobseeker mode)
- Profile completion tracking
- User settings
- Avatar/profile picture management

**Key Endpoints:**
- `GET /api/users/me`
- `PUT /api/users/me`
- `GET /api/users/:id/profile`
- `PUT /api/users/me/preferences`
- `DELETE /api/users/me`

**Database Tables:**
- `user_profiles` (id, user_id, full_name, bio, location, avatar_url)
- `user_preferences` (id, user_id, career_goals, learning_pace, notification_settings)
- `user_skills` (id, user_id, skill_name, proficiency_level)

---

### 3. Assessment Service

**Responsibilities:**
- Assessment creation and management
- Question bank management
- Assessment session handling
- Adaptive difficulty adjustment
- Answer submission and validation
- Scoring and result calculation

**Key Endpoints:**
- `GET /api/assessments` (list available assessments)
- `GET /api/assessments/:id` (get assessment details)
- `POST /api/assessments/:id/start` (start assessment session)
- `POST /api/assessments/sessions/:sessionId/answers` (submit answer)
- `GET /api/assessments/sessions/:sessionId/results` (get results)
- `PUT /api/assessments/sessions/:sessionId/pause` (pause assessment)

**Database Tables:**
- `assessments` (id, title, description, skill_domain, difficulty, question_count)
- `questions` (id, assessment_id, type, content, options, correct_answer, difficulty)
- `assessment_sessions` (id, user_id, assessment_id, started_at, completed_at, status, time_taken)
- `user_answers` (id, session_id, question_id, answer, is_correct, time_taken)
- `assessment_results` (id, session_id, user_id, score, time_taken, skill_gaps)

**Adaptive Testing Logic:**
```javascript
// Pseudocode for adaptive algorithm
function getNextQuestion(session, previousAnswer) {
  if (previousAnswer.isCorrect) {
    return getQuestionWithDifficulty(session.currentDifficulty + 1);
  } else {
    return getQuestionWithDifficulty(session.currentDifficulty - 1);
  }
}
```

---

### 4. Learning Service

**Responsibilities:**
- Personalized roadmap generation
- Learning path recommendations
- Course catalog management
- Progress tracking
- Content consumption tracking

**Key Endpoints:**
- `GET /api/learning/roadmap` (get personalized roadmap)
- `POST /api/learning/roadmap/generate` (generate new roadmap from assessment)
- `GET /api/learning/courses` (browse courses)
- `GET /api/learning/courses/:id`
- `POST /api/learning/courses/:id/enroll`
- `PUT /api/learning/courses/:id/progress`

**Database Tables:**
- `roadmaps` (id, user_id, assessment_result_id, generated_at, status)
- `roadmap_items` (id, roadmap_id, skill_name, priority, resources)
- `courses` (id, title, description, provider, url, skill_tags, difficulty)
- `user_course_progress` (id, user_id, course_id, progress_percentage, completed_at)
- `learning_resources` (id, title, type, url, skill_tags, provider)

**Roadmap Generation Algorithm:**
```javascript
// Simplified roadmap generation flow
async function generateRoadmap(assessmentResult) {
  const skillGaps = identifySkillGaps(assessmentResult);
  const userGoals = getUserCareerGoals(assessmentResult.userId);

  // Call AI service to generate personalized path
  const aiRoadmap = await aiService.generateRoadmap({
    skillGaps,
    userGoals,
    currentLevel: assessmentResult.overallScore
  });

  // Enrich with real courses
  const enrichedRoadmap = await enrichWithCourses(aiRoadmap);

  return enrichedRoadmap;
}
```

---

### 5. AI Integration Service

**Responsibilities:**
- OpenAI/Claude API communication
- Question generation
- Answer evaluation (open-ended questions)
- Code review and feedback
- Roadmap generation prompts
- Token usage tracking and cost management

**Key Functions:**
```javascript
// Internal service functions (not exposed as REST endpoints)

async function generateQuestions(skillDomain, difficulty, count) {
  const prompt = buildQuestionGenerationPrompt(skillDomain, difficulty);
  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "system", content: prompt }],
    temperature: 0.7
  });
  return parseQuestions(response.choices[0].message.content);
}

async function evaluateOpenEndedAnswer(question, userAnswer) {
  const prompt = buildEvaluationPrompt(question, userAnswer);
  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "system", content: prompt }],
    temperature: 0.3
  });
  return parseEvaluation(response.choices[0].message.content);
}

async function generateRoadmapWithAI(skillGaps, userGoals, currentLevel) {
  const prompt = buildRoadmapPrompt(skillGaps, userGoals, currentLevel);
  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "system", content: prompt }],
    temperature: 0.5
  });
  return parseRoadmap(response.choices[0].message.content);
}
```

**Database Tables:**
- `ai_requests` (id, service_type, tokens_used, cost, created_at)
- `ai_generated_content` (id, type, prompt, response, created_at)

**Cost Management:**
- Token usage tracking
- Daily/monthly budget limits
- Caching of common AI responses
- Fallback to rule-based logic if budget exceeded

---

### 6. Job Service

**Responsibilities:**
- Job listing aggregation from external sources
- Job search and filtering
- Job recommendation based on user skills
- Job application tracking (future)
- AI-powered job matching

**Key Endpoints:**
- `GET /api/jobs` (search jobs with filters)
- `GET /api/jobs/:id` (get job details)
- `GET /api/jobs/recommended` (personalized recommendations)
- `POST /api/jobs/:id/save` (bookmark job)
- `GET /api/jobs/saved` (get saved jobs)

**Database Tables:**
- `jobs` (id, title, company, description, requirements, location, salary, source, external_url, scraped_at)
- `job_skills` (id, job_id, skill_name, importance)
- `saved_jobs` (id, user_id, job_id, saved_at)
- `job_applications` (id, user_id, job_id, status, applied_at) [Future]

**Job Aggregation Strategy:**
```javascript
// Background job that runs periodically
async function aggregateJobs() {
  const sources = [
    { name: 'LinkedIn', scraper: linkedInScraper },
    { name: 'Wuzzuf', scraper: wuzzufScraper },
    { name: 'Bayt', scraper: baytScraper }
  ];

  for (const source of sources) {
    try {
      const jobs = await source.scraper.fetchJobs();
      await saveJobsToDatabase(jobs, source.name);
    } catch (error) {
      logger.error(`Failed to scrape ${source.name}:`, error);
    }
  }
}

// Run every 6 hours
schedule.every('6 hours').do(aggregateJobs);
```

**Matching Algorithm:**
```javascript
async function calculateJobMatch(userId, jobId) {
  const userSkills = await getUserSkills(userId);
  const jobRequirements = await getJobSkills(jobId);

  // Calculate skill overlap
  const matchScore = calculateSkillOverlap(userSkills, jobRequirements);

  // Factor in location, experience, etc.
  const adjustedScore = adjustForPreferences(matchScore, userId, jobId);

  return adjustedScore; // 0-100
}
```

---

### 7. Notification Service

**Responsibilities:**
- Email notifications
- In-app notifications
- Notification preferences management
- Scheduled reminders
- Event-driven notifications

**Key Endpoints:**
- `GET /api/notifications` (get user notifications)
- `PUT /api/notifications/:id/read` (mark as read)
- `PUT /api/notifications/read-all`
- `PUT /api/notifications/preferences`

**Database Tables:**
- `notifications` (id, user_id, type, title, message, read, created_at)
- `notification_preferences` (id, user_id, email_enabled, in_app_enabled, frequency)

**Notification Types:**
- `ROADMAP_READY` - "Your personalized learning path is ready!"
- `ASSESSMENT_REMINDER` - "You have pending assessments"
- `COURSE_PROGRESS` - "Great job! You're 50% through..."
- `NEW_JOB_MATCH` - "5 new jobs match your skills"
- `STREAK_REMINDER` - "Don't break your 7-day streak!"
- `WEEKLY_DIGEST` - "Your weekly learning summary"

**Email Templates:**
```javascript
const emailTemplates = {
  WELCOME: {
    subject: "Welcome to SkillPath AI!",
    template: "welcome.html"
  },
  ROADMAP_READY: {
    subject: "Your Learning Roadmap is Ready 🎯",
    template: "roadmap-ready.html"
  },
  ASSESSMENT_REMINDER: {
    subject: "Complete Your Assessment",
    template: "assessment-reminder.html"
  }
};
```

---

### 8. Analytics Service

**Responsibilities:**
- User behavior tracking
- Assessment performance analytics
- Learning progress metrics
- Platform usage statistics
- Admin dashboard data

**Key Endpoints:**
- `GET /api/analytics/dashboard` (admin overview)
- `GET /api/analytics/users/engagement`
- `GET /api/analytics/assessments/performance`
- `GET /api/analytics/courses/popularity`

**Database Tables:**
- `events` (id, user_id, event_type, event_data, created_at)
- `user_sessions` (id, user_id, started_at, ended_at, pages_viewed)
- `assessment_analytics` (id, assessment_id, avg_score, avg_time, completion_rate)

**Tracked Events:**
- User login/logout
- Assessment started/completed
- Course enrolled/completed
- Job viewed/saved
- Roadmap generated

---

## Technology Stack

### Backend Framework: **Node.js with Express.js**

**Why Node.js?**
- ✅ Fast development with JavaScript/TypeScript
- ✅ Excellent async I/O for API-heavy application
- ✅ Rich ecosystem (npm packages)
- ✅ Easy AI API integration
- ✅ JSON-native (perfect for REST APIs)
- ✅ Large community and resources

**Alternative Considered:** Python (Django/FastAPI)
- ❌ Slower development for MVP
- ✅ Better for ML/AI (but we're using external APIs)
- ❌ Less familiar to typical frontend developers

**Framework Structure:**
```
src/
├── config/           # Configuration files
├── controllers/      # Request handlers
├── services/         # Business logic
├── models/           # Database models (TypeORM/Sequelize)
├── middleware/       # Custom middleware
├── routes/           # API route definitions
├── utils/            # Helper functions
├── validators/       # Input validation schemas
└── types/            # TypeScript type definitions
```

---

### Database: **PostgreSQL 15+**

**Why PostgreSQL?**
- ✅ ACID compliance (data integrity)
- ✅ Rich data types (JSON, arrays, full-text search)
- ✅ Excellent performance for relational data
- ✅ Mature, battle-tested
- ✅ Free and open-source
- ✅ Great tooling and community

**Alternatives Considered:**
- MongoDB: ❌ Less suitable for complex relationships (users, assessments, courses)
- MySQL: ✅ Similar but PostgreSQL has better JSON support

**ORM: TypeORM or Prisma**
- TypeScript-first
- Migration management
- Type-safe queries

---

### Caching: **Redis 7+**

**Why Redis?**
- ✅ In-memory speed (microsecond latency)
- ✅ Session storage for JWT refresh tokens
- ✅ Rate limiting implementation
- ✅ Job queue (Bull/BullMQ)
- ✅ Caching frequently accessed data

**Use Cases:**
```javascript
// Session caching
await redis.setex(`session:${userId}`, 3600, JSON.stringify(userData));

// Rate limiting
const requestCount = await redis.incr(`rate-limit:${ip}:${minute}`);
if (requestCount > 100) throw new RateLimitError();

// Caching assessment questions
await redis.setex(`assessment:${id}`, 300, JSON.stringify(questions));

// Job queue for background tasks
await jobQueue.add('generate-roadmap', { userId, assessmentId });
```

---

### API Communication

**Style: RESTful API**

**Why REST?**
- ✅ Simple and well-understood
- ✅ Great tooling (Postman, Swagger)
- ✅ Easy to cache
- ✅ HTTP standards-based
- ✅ Easier for MVP development

**Alternative Considered:** GraphQL
- ❌ Overkill for MVP
- ❌ Steeper learning curve
- ✅ Could migrate later if needed

**API Documentation: Swagger/OpenAPI 3.0**

---

### AI/ML Integration

**Primary: OpenAI GPT-4 API**
- Question generation
- Answer evaluation
- Roadmap generation

**Alternative: Anthropic Claude API**
- Similar capabilities
- Potentially better for code evaluation
- Cost comparison needed

**Fallback Strategy:**
- Rule-based question bank
- Template-based roadmaps
- Cost/budget protection

---

### Authentication

**Strategy: JWT + Refresh Tokens**

**Access Token:**
- Short-lived (15 minutes)
- Contains user ID, role, permissions
- Stored in memory (not localStorage)

**Refresh Token:**
- Long-lived (7 days)
- Stored in httpOnly cookie
- Stored in Redis with user session data

**Flow:**
```
1. User logs in → Receive access + refresh token
2. Access token expires → Use refresh token to get new access token
3. Refresh token expires → User must log in again
4. User logs out → Invalidate refresh token in Redis
```

---

### File Storage

**MVP: Local file system**
- User avatars
- Generated certificates (future)

**Future: AWS S3 or Cloudinary**
- Scalable object storage
- CDN integration
- Image optimization

---

### Email Service

**MVP: Nodemailer + SMTP (Gmail/SendGrid free tier)**
- Transactional emails
- Notifications
- Password resets

**Future: SendGrid or AWS SES**
- Higher deliverability
- Analytics
- Template management

---

### Background Jobs

**Bull (Redis-based job queue)**

**Use Cases:**
- Generating roadmaps (AI API calls)
- Sending batch notifications
- Job scraping/aggregation
- Daily analytics calculations

```javascript
// Queue definition
const roadmapQueue = new Bull('roadmap-generation', {
  redis: redisConfig
});

// Job processor
roadmapQueue.process(async (job) => {
  const { userId, assessmentId } = job.data;
  await generateRoadmapForUser(userId, assessmentId);
});

// Add job to queue
await roadmapQueue.add({ userId, assessmentId }, {
  attempts: 3,
  backoff: { type: 'exponential', delay: 5000 }
});
```

---

### Logging and Monitoring

**MVP:**
- **Winston** (structured logging)
- **Morgan** (HTTP request logging)
- Basic error tracking

**Future:**
- Sentry (error tracking)
- Datadog / Prometheus (metrics)
- ELK stack (centralized logging)

---

### Testing

**Unit Tests: Jest**
**Integration Tests: Supertest**
**E2E Tests: Future (Playwright/Cypress)**

**Coverage Target: 70%+ for critical paths**

---

## Service Communication

### Internal Communication (MVP)

**Direct function calls** (modular monolith)

```javascript
// Example: Learning Service calling Assessment Service
import { getAssessmentResult } from './assessmentService';

async function generateRoadmap(userId, assessmentId) {
  const result = await getAssessmentResult(assessmentId);
  // ... roadmap generation logic
}
```

**Benefits:**
- No network latency
- Simple debugging
- Transaction support

---

### Event-Driven Communication (Future)

**Message Broker: RabbitMQ or Redis Pub/Sub**

```javascript
// Example: Assessment completed → Trigger roadmap generation
eventBus.emit('assessment.completed', {
  userId,
  assessmentId,
  score,
  skillGaps
});

// Listener in Learning Service
eventBus.on('assessment.completed', async (data) => {
  await queueRoadmapGeneration(data);
});
```

**Benefits:**
- Decoupled services
- Easier migration to microservices
- Async processing

---

## External Dependencies

### OpenAI / Claude API

**Rate Limits:** 10,000 requests/minute (GPT-4)
**Cost:** ~$0.03 per 1K tokens (input), $0.06 per 1K tokens (output)

**Budget Management:**
```javascript
const MONTHLY_BUDGET = 50; // $50/month
const COST_PER_QUESTION = 0.05; // ~$0.05 per AI-generated question

async function checkBudget() {
  const monthlySpend = await getMonthlyAISpend();
  if (monthlySpend >= MONTHLY_BUDGET) {
    throw new BudgetExceededError('Monthly AI budget exceeded');
  }
}
```

---

### Job Aggregation APIs

**LinkedIn Jobs API:**
- Requires partnership (not available publicly)
- Fallback: Web scraping with rate limiting

**Wuzzuf API:**
- No official API (web scraping)
- Respect robots.txt and rate limits

**Bayt API:**
- Check for API access or scraping

**Scraping Strategy:**
```javascript
// Use Puppeteer or Cheerio for scraping
const puppeteer = require('puppeteer');

async function scrapeWuzzuf() {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://wuzzuf.net/jobs/egypt');

  const jobs = await page.evaluate(() => {
    // Extract job data from DOM
  });

  await browser.close();
  return jobs;
}

// Run with rate limiting: 1 request per 5 seconds
```

---

## Security Architecture

### Authentication Security

**Password Security:**
- bcrypt hashing (cost factor: 12)
- Minimum password requirements (8+ chars, complexity)
- Password reset with time-limited tokens

**Token Security:**
- JWT with HS256 algorithm (symmetric)
- Short-lived access tokens (15 min)
- Refresh token rotation
- Token blacklisting on logout

**Session Security:**
- httpOnly cookies for refresh tokens
- SameSite=Strict to prevent CSRF
- Secure flag in production (HTTPS only)

---

### API Security

**Rate Limiting:**
```javascript
// Express rate limiter
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests, please try again later'
});

app.use('/api/', limiter);
```

**Input Validation:**
```javascript
// Using Joi or Zod for validation
const registerSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).required(),
  fullName: Joi.string().min(2).max(100).required()
});

app.post('/api/auth/register', validate(registerSchema), registerController);
```

**CORS Configuration:**
```javascript
const cors = require('cors');

app.use(cors({
  origin: process.env.FRONTEND_URL, // Only allow frontend domain
  credentials: true, // Allow cookies
  optionsSuccessStatus: 200
}));
```

**SQL Injection Prevention:**
- Use ORM (TypeORM/Prisma) with parameterized queries
- Never concatenate user input into SQL queries

**XSS Prevention:**
- Sanitize user input
- Content Security Policy headers
- Escape output in templates

---

### Data Security

**Encryption at Rest:**
- Database encryption (PostgreSQL TDE)
- Sensitive fields encrypted (e.g., API keys)

**Encryption in Transit:**
- HTTPS everywhere (Let's Encrypt SSL)
- TLS 1.2+ only

**Sensitive Data Handling:**
```javascript
// Example: Encrypting user API keys
const crypto = require('crypto');

function encrypt(text) {
  const cipher = crypto.createCipheriv('aes-256-cbc', KEY, IV);
  return cipher.update(text, 'utf8', 'hex') + cipher.final('hex');
}

function decrypt(encrypted) {
  const decipher = crypto.createDecipheriv('aes-256-cbc', KEY, IV);
  return decipher.update(encrypted, 'hex', 'utf8') + decipher.final('utf8');
}
```

---

### OWASP Top 10 Mitigation

| Vulnerability | Mitigation Strategy |
|--------------|---------------------|
| **Injection** | ORM with parameterized queries, input validation |
| **Broken Auth** | JWT + refresh tokens, rate limiting, MFA (future) |
| **Sensitive Data Exposure** | HTTPS, encryption at rest, secure headers |
| **XML External Entities** | Not applicable (JSON API) |
| **Broken Access Control** | Role-based access control (RBAC) middleware |
| **Security Misconfiguration** | Security headers (Helmet.js), minimize exposed info |
| **XSS** | Input sanitization, Content Security Policy |
| **Insecure Deserialization** | Validate JSON structure, avoid eval() |
| **Using Components with Known Vulnerabilities** | npm audit, Dependabot, regular updates |
| **Insufficient Logging** | Comprehensive logging with Winston, audit trails |

---

## Scalability Strategy

### Vertical Scaling (MVP → 10K users)

**Server Specs:**
- Start: 2 vCPU, 4GB RAM (DigitalOcean $24/month)
- Scale to: 4 vCPU, 8GB RAM ($48/month)

**Database:**
- Start: Shared PostgreSQL instance
- Scale: Dedicated database server

---

### Horizontal Scaling (10K+ users)

**Load Balancing:**
```
                    ┌─────────────┐
     ────────────>  │   Nginx     │
                    │ Load Balancer│
                    └─────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ App      │    │ App      │    │ App      │
    │ Server 1 │    │ Server 2 │    │ Server 3 │
    └──────────┘    └──────────┘    └──────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                  ┌───────────────┐
                  │   PostgreSQL  │
                  │   (Primary)   │
                  └───────────────┘
                          │
                  ┌───────┴────────┐
                  ▼                ▼
            ┌──────────┐     ┌──────────┐
            │ Read     │     │ Read     │
            │ Replica  │     │ Replica  │
            └──────────┘     └──────────┘
```

---

### Caching Strategy

**Multi-Layer Caching:**

1. **Application Layer Cache (Redis)**
   - User sessions
   - Assessment questions
   - Course catalog
   - Job listings

2. **Database Query Cache**
   - Frequently accessed data
   - Read replicas for heavy queries

3. **CDN Cache (Future)**
   - Static assets
   - Media files
   - API responses (where appropriate)

**Cache Invalidation:**
```javascript
// Example: Invalidate cache when data changes
async function updateUserProfile(userId, updates) {
  await db.users.update(userId, updates);
  await redis.del(`user:${userId}`); // Invalidate cache
}

// Lazy loading pattern
async function getUserProfile(userId) {
  const cached = await redis.get(`user:${userId}`);
  if (cached) return JSON.parse(cached);

  const user = await db.users.findById(userId);
  await redis.setex(`user:${userId}`, 3600, JSON.stringify(user));
  return user;
}
```

---

### Database Optimization

**Indexing Strategy:**
```sql
-- Critical indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_assessment_sessions_user_id ON assessment_sessions(user_id);
CREATE INDEX idx_user_answers_session_id ON user_answers(session_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);

-- Composite indexes for common queries
CREATE INDEX idx_assessments_domain_difficulty ON assessments(skill_domain, difficulty);
CREATE INDEX idx_courses_skill_tags ON courses USING GIN(skill_tags);
```

**Connection Pooling:**
```javascript
const pool = new Pool({
  max: 20, // Maximum connections
  min: 5,  // Minimum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});
```

**Query Optimization:**
- Use EXPLAIN ANALYZE for slow queries
- Avoid N+1 queries (use JOIN or batch loading)
- Pagination for large result sets
- Lazy loading for related data

---

### Monitoring & Performance

**Key Metrics:**
- API response time (p50, p95, p99)
- Database query time
- Cache hit rate
- Error rate
- Active users
- Background job queue length

**Alerting:**
- Response time > 1 second
- Error rate > 1%
- Database CPU > 80%
- Disk space < 20%

---

## Deployment Architecture

### MVP Deployment (Single Server)

```
┌─────────────────────────────────────────────────────┐
│              VPS Server (DigitalOcean)               │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Docker Compose                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │  Nginx   │  │ Node.js  │  │PostgreSQL│  │    │
│  │  │  (80,    │  │  App     │  │          │  │    │
│  │  │   443)   │  │  (3000)  │  │  (5432)  │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  │    │
│  │                                              │    │
│  │  ┌──────────┐                                │    │
│  │  │  Redis   │                                │    │
│  │  │  (6379)  │                                │    │
│  │  └──────────┘                                │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

  app:
    build: .
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://user:pass@postgres:5432/skillpath
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: skillpath
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

---

### CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Run linter
        run: npm run lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/skillpath-backend
            git pull origin main
            docker-compose down
            docker-compose up -d --build
```

---

## Next Steps: Implementation Roadmap

### Week 1-2: Foundation
1. Set up project structure
2. Configure TypeScript, ESLint, Prettier
3. Set up PostgreSQL + Redis locally
4. Implement authentication service (JWT)
5. Create user service and profiles

### Week 3-4: Assessment System
1. Design database schema for assessments
2. Implement question bank management
3. Build assessment session logic
4. Add adaptive testing algorithm
5. Create scoring system

### Week 5-6: AI & Learning Paths
1. Integrate OpenAI/Claude API
2. Build AI service layer
3. Implement roadmap generation
4. Create learning service
5. Add course recommendation logic

### Week 7: Job Marketplace
1. Set up job aggregation (scraping)
2. Build job search and filtering
3. Implement matching algorithm
4. Add job recommendations

### Week 8: Polish & Deploy
1. Add notification system
2. Implement analytics tracking
3. Write integration tests
4. Deploy to production server
5. Set up monitoring and logging

---

**Architecture Document Prepared By:** SkillPath AI Development Team
**Review Status:** Pending stakeholder approval
**Next Review Date:** Before development kickoff
