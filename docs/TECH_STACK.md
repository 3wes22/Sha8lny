# Sha8alny - Technology Stack

## Overview
This document outlines the complete technology stack for the Sha8alny platform, including backend, frontend, database, AI/ML infrastructure, and supporting services.

---

## Backend

### Core Framework
- **Django (Latest Stable Version)**
  - Python web framework for rapid development
  - Strong ORM capabilities
  - Built-in admin interface for content management
  - Excellent security features out of the box

### Key Packages

**API Development:**
- **Django REST Framework (DRF)**
  - RESTful API development
  - Serialization and validation
  - Authentication and permissions
  - Browsable API interface

**Recommended Additional Packages:**
- **django-cors-headers**: Handle Cross-Origin Resource Sharing for frontend communication
- **djangorestframework-simplejwt**: JWT authentication implementation
- **celery**: Asynchronous task queue for:
  - AI model processing
  - Email notifications
  - Job market data fetching
  - Background roadmap generation
- **django-celery-beat**: Periodic task scheduling (for scheduled job scraping, etc.)
- **redis**: Message broker for Celery and caching
- **requests** / **httpx**: HTTP client for external API calls
- **beautifulsoup4** / **scrapy**: Web scraping for job platforms

**Database:**
- **psycopg2-binary**: PostgreSQL adapter for Python/Django

**AI/ML Integration:**
- **openai**: OpenAI API client (if using GPT models)
- **anthropic**: Anthropic API client (if using Claude)
- **langchain**: LLM orchestration and chaining
- **pinecone-client**: Vector database client for RAG
- **sentence-transformers**: For embeddings generation
- **transformers**: Hugging Face library for custom models

**Testing & Quality:**
- **pytest-django**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

---

## Frontend

### Core Framework
- **React 18+**
  - Component-based architecture
  - Rich ecosystem and community support
  - Excellent for dynamic, interactive UIs

### Language
- **TypeScript**
  - Type safety for large-scale applications
  - Better IDE support and autocomplete
  - Reduced runtime errors
  - Improved code documentation

### Architecture
- **Multi-Page Application (MPA)**
  - Server-side rendering or static generation for better SEO
  - Better initial page load performance
  - More traditional navigation patterns

### Build Tools & Framework Options

**Recommended: Next.js (React Framework)**
- Server-side rendering (SSR) and static site generation (SSG)
- API routes for backend-for-frontend (BFF) pattern
- Built-in routing
- Image optimization
- TypeScript support out of the box

**Alternative: Vite + React Router**
- Faster development experience
- Lightweight and flexible
- Manual routing configuration with React Router

### Key Libraries

**UI & Styling:**
- **TailwindCSS** or **Material-UI (MUI)**: Component styling
- **Radix UI** or **Headless UI**: Accessible component primitives
- **Framer Motion**: Animations and transitions
- **react-icons**: Icon library

**State Management:**
- **React Query (TanStack Query)**: Server state management, caching, and synchronization
- **Zustand** or **Redux Toolkit**: Client state management (if needed for complex state)

**Form Handling:**
- **React Hook Form**: Performant form validation
- **Zod**: TypeScript-first schema validation

**Data Visualization:**
- **Recharts** or **Chart.js**: Progress tracking visualizations
- **React-Flow**: Visual roadmap/learning path diagrams

**HTTP Client:**
- **Axios** or **Fetch API with React Query**: API communication

**Authentication:**
- **Auth0 React SDK**: Integration with Auth0
- Custom JWT handling utilities

**Additional Tools:**
- **ESLint**: TypeScript/React linting
- **Prettier**: Code formatting
- **Husky**: Git hooks for pre-commit checks

---

## Database

### Primary Database
- **PostgreSQL (Latest Stable)**
  - Self-hosted deployment
  - Relational database for structured data
  - JSONB support for flexible schema where needed
  - Excellent performance and reliability
  - Strong ACID compliance

### Why PostgreSQL?
- Better data integrity for user profiles and career data
- Complex querying capabilities for job matching
- Strong relationships between entities (users, skills, courses, jobs)
- Better transaction support
- Proven scalability

### Database Tools
- **pgAdmin**: Database administration interface
- **Django ORM**: Primary database interaction layer
- **Django Migrations**: Schema version control

### Future Considerations
- **Read Replicas**: For scaling read-heavy operations
- **Connection Pooling (PgBouncer)**: Optimize database connections
- **TimescaleDB Extension**: If time-series data becomes important (user activity tracking)

---

## AI/ML Infrastructure

### LLM Strategy
**Hybrid Multi-Model Approach:**

1. **Commercial LLM APIs:**
   - **OpenAI GPT-4/GPT-4-Turbo**: Complex reasoning, roadmap generation
   - **Anthropic Claude**: Long-context tasks, detailed assessments
   - **Google Gemini**: Cost-effective alternative for specific tasks
   
2. **Custom Fine-Tuned Models:**
   - Domain-specific models trained on career/education data
   - Egyptian job market specific understanding
   - Cost optimization for high-frequency operations

3. **Open-Source Models (Future):**
   - **Llama 2/3**: Self-hosted for privacy-sensitive operations
   - **Mistral**: European alternative with good performance
   - Self-hosted deployment for cost control at scale

### RAG (Retrieval Augmented Generation)
**Vector Database:**
- **Pinecone**: Managed vector database
  - Store course embeddings
  - Store job description embeddings
  - Store skill knowledge base
  - Fast similarity search

**RAG Pipeline:**
```
User Query → Embedding → Vector Search → Context Retrieval → 
LLM Augmented Generation → Response
```

**Embedding Models:**
- **OpenAI text-embedding-ada-002**: General purpose
- **Sentence-Transformers**: Open-source alternative
- Custom fine-tuned embeddings for domain specificity

### Model Fine-Tuning
**Planned Fine-Tuning:**
- Skill assessment accuracy
- Egyptian market terminology
- Career domain expertise
- Course recommendation optimization

**Tools:**
- **Hugging Face Transformers**: Training pipeline
- **Weights & Biases**: Experiment tracking
- **PyTorch** / **TensorFlow**: Model training

### AI Orchestration
- **LangChain**: Chain complex AI workflows
- **LangSmith**: Monitoring and debugging AI chains
- **Prompt Templates**: Version-controlled prompt engineering

---

## External Integrations

### Job Market Data Sources

**API-Based (When Available):**
- **LinkedIn Jobs API**: (Requires partnership/access)
- **Bayt API**: If available
- **Other regional job boards**: As partnerships develop

**Web Scraping (Current Strategy):**
- **Wuzzuf.net**: Egyptian job market leader
- **Bayt.com**: Regional job platform
- **LinkedIn Jobs**: Scraping as fallback
- Additional Egyptian job boards

**Scraping Tools:**
- **Scrapy**: Python scraping framework
- **Selenium**: For JavaScript-heavy sites
- **BeautifulSoup**: HTML parsing
- **Playwright**: Modern browser automation

**Data Pipeline:**
- **Celery Beat**: Scheduled scraping tasks
- **Redis**: Caching scraped job data
- **Rate Limiting**: Respect website terms and avoid blocks
- **Proxy Rotation**: If needed for scaling

### Learning Resource APIs

**Platform Integrations:**
- **Udemy Affiliate API**: Course links and data
- **Coursera API**: Course catalog (if available)
- **YouTube Data API**: Educational video content
- **edX API**: Open course content
- Additional platforms as needed

---

## Authentication & Authorization

### Primary Authentication
- **Auth0**
  - Social login (Google, LinkedIn, Facebook)
  - Email/password authentication
  - Multi-factor authentication (MFA)
  - User management dashboard
  - Secure token handling

### Custom JWT Implementation
- **Backend JWT Generation**: Django REST Framework SimpleJWT
- **Token Storage**: HTTP-only cookies (secure) or localStorage (convenience)
- **Refresh Token Strategy**: Long-lived refresh, short-lived access tokens
- **Role-Based Access Control (RBAC)**: User permissions and roles

### Session Management
- **Redis**: Session storage for scalability
- **Django Sessions**: Fallback/hybrid approach

---

## File Storage & Media

### Strategy
**Database Storage (Initial Approach):**
- Resumes/CVs stored as database attributes (BLOB/BYTEA in PostgreSQL)
- Portfolios stored as JSON/text in database
- User profile images in database

**Considerations:**
- **Pros**: Simple architecture, no external dependencies
- **Cons**: Database size growth, backup complexity, less scalable

**Future Migration Path (When Scale Requires):**
- **AWS S3**: Scalable object storage
- **Cloudinary**: Image optimization and CDN
- Keep database references to external file URLs

---

## Hosting & Infrastructure

### Hosting Provider
- **Hostinger**
  - VPS or dedicated hosting
  - Cost-effective for MVP stage
  - Sufficient for moderate traffic

### Infrastructure Components

**Backend Hosting:**
- Django application server (Gunicorn/uWSGI)
- Nginx reverse proxy
- PostgreSQL database
- Redis cache

**Frontend Hosting:**
- Static files served via Nginx
- Or Next.js server deployment

**Future Scaling Options:**
- **Containerization**: Docker for consistent deployments
- **Orchestration**: Kubernetes if massive scale needed
- **CDN**: Cloudflare for static assets and DDoS protection
- **Load Balancing**: Multiple application servers

---

## Email Service

**Status:** TBD (To Be Determined)

**Use Cases:**
- Account verification emails
- Password reset
- Learning path milestones
- Job match notifications
- Community notifications
- Weekly progress reports

**Options to Consider:**
- **SendGrid**: 100 emails/day free, easy integration
- **AWS SES**: $0.10 per 1,000 emails, requires AWS account
- **Mailgun**: Developer-friendly, good deliverability
- **Postmark**: Focus on transactional emails
- **Django SMTP**: Simple setup with Gmail/custom SMTP server

**Recommendation:** Start with SendGrid free tier or Django SMTP for MVP, migrate to dedicated service as user base grows.

---

## Monitoring & Analytics

### Application Monitoring
**To Be Implemented:**
- **Sentry**: Error tracking and performance monitoring
- **LogDNA/Datadog**: Log aggregation and analysis
- **Prometheus + Grafana**: Metrics and dashboards

### User Analytics
**Options:**
- **Google Analytics**: User behavior tracking
- **Mixpanel**: Product analytics
- **PostHog**: Open-source analytics alternative
- Custom event tracking via Django

### AI/LLM Monitoring
- **LangSmith**: LLM chain debugging
- **Weights & Biases**: Model performance
- Custom logging for token usage and costs

---

## Development Tools

### Version Control
- **Git**: Source code management
- **GitHub/GitLab**: Repository hosting and CI/CD

### CI/CD Pipeline
- **GitHub Actions** or **GitLab CI**: Automated testing and deployment
- **Pre-commit hooks**: Code quality checks before commit
- **Automated testing**: Run test suites on every push

### Code Quality
- **Black**: Python code formatting
- **Flake8/Pylint**: Python linting
- **ESLint**: TypeScript/React linting
- **Prettier**: Frontend code formatting
- **mypy**: Python type checking

### API Documentation
- **Django REST Framework**: Auto-generated API docs
- **Swagger/OpenAPI**: API specification
- **Postman**: API testing and documentation

### Development Environment
- **Docker Compose**: Local development environment
- **Virtual environments**: Python dependency isolation
- **npm/yarn**: Frontend dependency management

---

## Security Considerations

### Backend Security
- Django security middleware enabled
- HTTPS/TLS encryption (Let's Encrypt)
- SQL injection protection (Django ORM)
- XSS protection
- CSRF protection
- Rate limiting (django-ratelimit)
- API authentication required

### Frontend Security
- Environment variables for sensitive data
- XSS prevention (React default escaping)
- Secure token storage
- HTTPS only
- Content Security Policy (CSP)

### Data Protection
- Password hashing (Django default PBKDF2)
- Encrypted database backups
- GDPR compliance considerations
- User data export capabilities

### AI Security
- API key rotation
- Rate limiting for LLM calls
- Prompt injection prevention
- Output validation and sanitization

---

## Cost Optimization Strategy

### LLM Costs
- Cache frequent responses
- Use cheaper models for simple tasks
- Batch processing where possible
- Monitor token usage closely
- Implement request quotas

### Infrastructure Costs
- Start with single server (Hostinger VPS)
- Scale horizontally when needed
- Use caching aggressively (Redis)
- Optimize database queries
- CDN for static assets

### Third-Party Services
- Use free tiers initially
- Monitor usage to avoid overages
- Consider self-hosted alternatives for scale

---

## Technology Decision Rationale

### Why This Stack?

**Django + PostgreSQL:**
- Mature, battle-tested technologies
- Rapid development capabilities
- Strong ecosystem
- Excellent for data-driven applications
- PostgreSQL reliability and query power

**React + TypeScript:**
- Most popular frontend framework
- Type safety reduces bugs
- Large talent pool
- Extensive library ecosystem

**Multi-Model AI Approach:**
- Flexibility to optimize for cost and performance
- Avoid vendor lock-in
- Use best model for each task
- Future-proof with custom models

**Hostinger (MVP Phase):**
- Cost-effective for early stage
- Easy migration path to cloud providers
- Sufficient for initial user base

---

## Migration & Scaling Path

### Phase 1 (MVP): Current Stack
- Single VPS server
- Monolithic Django application
- PostgreSQL on same server
- Manual deployments

### Phase 2 (Growth):
- Separate database server
- Redis caching layer
- Containerization (Docker)
- Automated deployments
- CDN for static assets

### Phase 3 (Scale):
- Extract specific modules to microservices (if bottlenecks identified)
- Load balancers
- Database read replicas
- Cloud migration (AWS/GCP/Azure)
- Kubernetes orchestration (if microservices extracted)

---

*Last Updated: November 2025*  
*Status: Planning Phase - Stack subject to refinement based on development needs*
