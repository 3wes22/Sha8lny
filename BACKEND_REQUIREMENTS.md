# SkillPath AI - Backend Architecture Requirements

> **Document Version:** 1.0
> **Last Updated:** November 4, 2025
> **Status:** MVP Planning Phase

---

## Executive Summary

SkillPath AI is an educational platform targeting the Egyptian market with AI-driven skill assessments, personalized learning paths, and job marketplace integration. This document outlines the backend requirements and technical constraints for MVP development.

**Key Technical Constraints:**
- **Budget:** $0 (minimal infrastructure costs)
- **Timeline:** 2-month MVP development starting mid-year vacation
- **Team:** Small development team
- **Scale:** Start with hundreds of users, design for future growth
- **Region:** Egypt initially, MENA expansion planned

---

## 1. Core Features & MVP Scope

### MVP Priorities (Phase 1)

**Must-Have Features:**
1. **AI-Driven Skill Assessments**
   - Adaptive testing with 5 question types
   - Time tracking (not strictly enforced)
   - Scoring based on correctness and time
   - No proctoring (webcam/screen monitoring)

2. **User Authentication & Profiles**
   - Secure registration and login
   - Profile management for learners and jobseekers
   - Basic user preferences

3. **Personalized Learning Paths**
   - Assessment → Roadmap pipeline
   - AI-generated personalized roadmaps
   - Course recommendations based on user history

### Future Phases (Post-MVP)

**Phase 2:**
- Job marketplace integration
- Corporate training portal
- Payment integration (Fawry, Paymob, Stripe, PayPal)

**Phase 3:**
- Advanced analytics and AI personalization
- Certification system
- Gamification features
- Real-time chat and messaging

### Backend Features Not Yet in Frontend

- Adaptive testing logic engine
- Assessment result → roadmap generation pipeline
- AI-powered recommendation engine
- Context-based LLM integration for personalized content

---

## 2. User Roles & Access Control

### Primary Roles (MVP)

| Role | Permissions | Description |
|------|-------------|-------------|
| **Administrator** | Full system access | Platform management, content oversight, user management |
| **User** | Standard access | Base role for all registered users |
| **Learner** | Learning features | User focused on skill development |
| **Jobseeker** | Job + Learning features | User seeking employment opportunities |

### Future Roles (Post-MVP)
- Corporate Admin / HR Manager
- Content Creator / Instructor
- Recruiter / Employer
- Platform Moderator

---

## 3. AI/ML Integration Strategy

### Assessment Generation & Evaluation
- **Technology:** OpenAI GPT-4 / Claude API
- **Use Cases:**
  - Dynamic question generation
  - Open-ended answer evaluation
  - Code review and feedback
- **Custom Logic:** Adaptive difficulty adjustment based on performance

### Personalized Roadmap Generation
- **Input:** User assessment results, skill gaps, goals
- **Processing:** Custom ML model (likely rule-based initially, ML later)
- **Output:** Structured learning path with recommended courses

### Code Assessment Auto-Grading
- **Qualitative:** AI-based code review (GPT-4/Claude)
- **Quantitative:** Test runners for automated validation

### Recommendation Engine
- **Inputs:** User history, preferences, performance data
- **Algorithm:** Collaborative filtering + content-based filtering
- **Integration:** With course catalog and job marketplace

---

## 4. Assessment System Specifications

### Time Management
- Time tracking enabled for all assessments
- **No strict enforcement:** Users can pause
- Pause triggers warning: "Time is a scoring factor"
- Scoring formula includes time as weighted component

### Adaptive Testing
- **Enabled:** Yes
- **Logic:**
  - Start with medium difficulty
  - Adjust based on previous answers
  - Algorithm: Item Response Theory (IRT) or custom rule-based

### Question Types (5 Types)
1. Multiple Choice Questions (MCQ)
2. True/False
3. Code Completion
4. Open-ended Short Answer
5. Practical Code Challenge

### Proctoring
- **MVP:** None
- **Future:** Optional AI-based behavioral analysis (no webcam)

### Certificates
- **MVP:** Not included
- **Future:** Auto-generated certificates with verification codes

---

## 5. Job Marketplace Architecture

### Data Sourcing Strategy
- **Primary:** External job aggregation
- **Sources:**
  - LinkedIn Jobs API (if available)
  - Wuzzuf (scraping or API)
  - Bayt (scraping or API)
  - Other Egyptian job boards

### Job Posting
- **MVP:** No direct employer posting
- **Future:** Employer dashboard for direct job creation

### Matching Algorithm
- **Hybrid Approach:**
  - **Filter-based:** Skills, location, experience level
  - **AI-based:** Semantic matching using embeddings
  - **Scoring:** Compatibility score (0-100%)

### Application Flow
- MVP: Redirect to external job listings
- Future: In-platform application tracking system

---

## 6. Monetization & Payment Integration

### MVP Phase
- **Model:** Freemium
- All assessments and basic learning paths: **Free**

### Future Monetization
- **Premium Tiers:**
  - Advanced assessments
  - Detailed analytics
  - Priority support
  - Certification

- **Payment Gateways:**
  - Fawry (Egypt-specific)
  - Paymob (MENA region)
  - Stripe (international)
  - PayPal (backup)

- **Currency Support:**
  - Primary: EGP (Egyptian Pound)
  - Optional: USD for international users

---

## 7. Scale & Performance Requirements

### User Projections (Conservative Estimates)

| Timeline | Registered Users | Daily Active Users | Peak Concurrent |
|----------|-----------------|-------------------|----------------|
| **Launch** | 100-500 | 20-50 | 10-20 |
| **3 months** | 1,000-2,000 | 100-200 | 30-50 |
| **6 months** | 3,000-5,000 | 300-500 | 50-100 |
| **1 year** | 10,000-20,000 | 1,000-2,000 | 200-300 |

### Performance Targets
- **API Response Time:** < 200ms (95th percentile)
- **Assessment Load Time:** < 1 second
- **Roadmap Generation:** < 5 seconds
- **Database Query Time:** < 50ms (average)

### Geographic Distribution
- **Primary:** Egypt (Cairo, Alexandria, Giza)
- **Future:** MENA region (Saudi Arabia, UAE, Jordan)

### Data Volume Estimates
- **Assessments:** ~50-100 per skill domain
- **Questions:** ~500-1,000 initially
- **User Responses:** ~10,000-50,000 in first 6 months
- **Job Listings:** ~1,000-5,000 aggregated

---

## 8. Data Sensitivity & Compliance

### Data Classification

| Data Type | Sensitivity | Handling |
|-----------|-------------|----------|
| User credentials | High | Hashed passwords, encrypted storage |
| Assessment results | Medium | User-controlled visibility |
| Personal profiles | Medium | GDPR-compliant (if needed) |
| Learning history | Low | Analytics-enabled |

### Compliance Requirements
- **Egyptian Data Protection Law** (if storing sensitive data)
- **GDPR:** Not required for MVP (Egypt-only), but design for future compatibility
- **Data Residency:** Prefer Egyptian or regional hosting for latency

### Privacy Policy
- User data ownership
- Right to data export
- Right to account deletion
- Transparent AI usage disclosure

---

## 9. Real-Time & Interactive Features

### Notification System
- **Inspiration:** Duolingo-style engagement
- **Types:**
  - "You have pending lessons" reminders
  - "Congratulations on completing X" celebrations
  - "Your roadmap is ready" notifications
  - Daily/weekly streaks and progress updates

### Delivery Channels
- **MVP:** In-app notifications + Email
- **Future:** SMS (via Twilio or local provider)

### Engagement Triggers
- User inactivity (3 days, 7 days)
- Milestone achievements
- New recommended content
- Assessment completion reminders

### Chat/Messaging
- **MVP:** Not included
- **Future:** Learner-instructor messaging, support chat

---

## 10. Content Management System

### Assessment Management
- **Creation:** AI-generated questions with admin review
- **Approval Workflow:** Basic admin monitoring (not required for MVP)
- **Versioning:** Track assessment changes over time
- **Storage:** Questions stored as structured JSON

### Course Content
- **Types Supported:**
  - Video embeds (YouTube, Vimeo)
  - Text-based lessons (Markdown)
  - Code snippets (syntax highlighting)
  - External links (Coursera, Udemy, etc.)

### Media Storage
- **MVP:** External URLs (YouTube, public CDN)
- **Future:** Self-hosted media (AWS S3, Cloudinary)

### Content Updates
- Admins can edit assessments
- Version history maintained
- No manual approval flow for AI-generated content

---

## 11. Third-Party Integrations

### MVP Phase
**None required** — All functionality will be self-contained or use free/public APIs.

### Future Integrations

| Service | Purpose | Priority |
|---------|---------|----------|
| **OpenAI / Anthropic** | AI assessment & roadmap generation | High |
| **Fawry / Paymob** | Payment processing | Medium |
| **SendGrid / AWS SES** | Email delivery | Medium |
| **Twilio** | SMS notifications | Low |
| **Cloudinary / S3** | Media storage | Medium |
| **Google Analytics** | User analytics | Low |
| **Mixpanel / Amplitude** | Product analytics | Low |

---

## 12. Infrastructure & DevOps Strategy

### Hosting Approach
- **MVP:** Local or minimal VPS hosting (e.g., DigitalOcean, Hetzner)
- **Budget:** $0-$20/month initially
- **Region:** Egypt or nearby (UAE/Germany for low latency)

### Cloud Provider
- **MVP:** None (self-hosted or minimal VPS)
- **Future:** AWS, Google Cloud, or Azure (when budget allows)

### Containerization
- **Docker:** Yes, for consistent dev/prod environments
- **Docker Compose:** For local development
- **Kubernetes:** Not needed for MVP (overkill)

### CI/CD Pipeline
- **MVP:** Manual deployments or basic GitHub Actions
- **Future:** Automated testing, staging, and production deployments

### Monitoring & Logging
- **MVP:** Basic logging (Winston, Pino)
- **Future:** Centralized logging (ELK stack, Datadog, Sentry)

### Backup Strategy
- **Database Backups:** Daily automated backups
- **Retention:** 30 days minimum
- **Recovery:** Tested disaster recovery plan

---

## 13. Development Timeline

### Phase 1: MVP Development (2 months)

| Week | Focus Area |
|------|-----------|
| **Week 1-2** | Backend architecture setup, database design, authentication |
| **Week 3-4** | Assessment system, adaptive testing logic |
| **Week 5-6** | AI integration (OpenAI/Claude), roadmap generation |
| **Week 7** | Job marketplace aggregation, recommendation engine |
| **Week 8** | Testing, bug fixes, deployment preparation |

### Phase 2: Beta Launch (1 month)
- User testing with 50-100 beta users
- Bug fixes and performance optimization
- Feedback integration

### Phase 3: Full Launch
- Public release
- Marketing and user acquisition
- Feature expansion based on user feedback

---

## Key Technical Decisions Summary

| Decision Area | Choice | Rationale |
|--------------|--------|-----------|
| **Backend Framework** | TBD (Node.js/Python preferred) | Team expertise, rapid development |
| **Database** | PostgreSQL | Relational data, ACID compliance, scalability |
| **Caching** | Redis | Session management, performance boost |
| **AI Provider** | OpenAI GPT-4 / Claude | Best-in-class language models |
| **Authentication** | JWT + Refresh Tokens | Stateless, scalable |
| **API Style** | RESTful | Simpler for MVP, well-documented |
| **Hosting** | VPS (DigitalOcean/Hetzner) | Cost-effective for MVP |
| **Deployment** | Docker + GitHub Actions | Consistency, automation |

---

## Next Steps

1. **Finalize technology stack** based on team expertise
2. **Design detailed database schema** (entities, relationships, indexes)
3. **Create API specification** (OpenAPI/Swagger documentation)
4. **Set up development environment** (Docker, local databases)
5. **Implement authentication system** (user registration, login, JWT)
6. **Build assessment engine** (adaptive testing logic)
7. **Integrate AI services** (OpenAI/Claude for question generation)
8. **Develop recommendation system** (roadmap generation)
9. **Implement job aggregation** (scraping/API integration)
10. **Testing and deployment** (unit tests, integration tests, staging environment)

---

**Document prepared by:** SkillPath AI Development Team
**For questions or clarifications:** Contact project lead
