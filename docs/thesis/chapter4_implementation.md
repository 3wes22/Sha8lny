# CHAPTER 4: IMPLEMENTATION AND PRELIMINARY RESULTS

---

## 4.1 Programming Languages and Tools

This section presents the technology choices for the Sha8lny platform, justified by project requirements and industry best practices.

### 4.1.1 Backend Stack

The backend uses Python 3.10+ with Django 5.0+, following a modular monolithic architecture. Django was selected for its rapid development capabilities, built-in security features, and strong ORM for database operations (Django Software Foundation, 2024).

**Table 4.1: Core Backend Technologies**

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Backend language with strong AI/ML ecosystem |
| Django | 5.0+ | Web framework with built-in admin and ORM |
| Django REST Framework | 3.14+ | RESTful API development |
| PostgreSQL | Latest | Primary database with JSONB support |
| Redis | 5.0+ | Caching and Celery message broker |
| Celery | 5.3+ | Asynchronous task processing for AI operations |

Key backend packages include JWT authentication (djangorestframework-simplejwt), Auth0 integration (authlib), API documentation (drf-spectacular), and web scraping tools (scrapy, selenium, beautifulsoup4).

### 4.1.2 Frontend Stack

The frontend uses React 18.3 with TypeScript 5.8, providing type safety and component-based architecture. Vite 5.4 serves as the build tool for fast development iteration.

**Table 4.2: Core Frontend Technologies**

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | Component-based UI framework |
| TypeScript | 5.8.3 | Static typing for error prevention |
| Vite | 5.4.19 | Fast build tool and dev server |
| Tailwind CSS | 3.4.18 | Utility-first styling |
| React Query | 5.83.0 | Server state management and caching |

The UI leverages Radix UI primitives for accessible components and react-hook-form with Zod for form validation.

### 4.1.3 AI/ML Stack

The AI component uses a local LLM approach to eliminate API costs. This follows the parameter-efficient fine-tuning paradigm introduced by Hu et al. (2022) with LoRA adapters.

**Table 4.3: AI/ML Technologies**

| Technology | Version | Purpose |
|------------|---------|---------|
| PyTorch | 2.1+ | Deep learning framework |
| Transformers | 4.35+ | Hugging Face model library |
| bitsandbytes | 0.41+ | 4-bit quantization (Dettmers et al., 2023) |
| PEFT | 0.6+ | Parameter-efficient fine-tuning |
| ChromaDB | 0.4+ | Vector database for RAG |
| LightGBM | 4.1+ | Gradient boosting for job ranking |

**Planned Model Specifications**

| Model | Parameters | Memory (4-bit) | Use Case |
|-------|------------|----------------|----------|
| LLaMA 3.1 8B | 8 billion | ~5 GB | Assessment generation (Touvron et al., 2023) |
| Mistral 7B | 7 billion | ~4.5 GB | Roadmap and RAG responses |
| Sentence-Transformers | 22 million | <500 MB | Semantic embeddings (Reimers & Gurevych, 2019) |

---

## 4.2 Code Structure

### 4.2.1 Repository Organization

The project follows a monorepo structure with three components:

```
Sha8lny/
├── Backend/          # Django REST API (10 modules)
├── Frontend/         # React + TypeScript SPA
├── ai-models/        # Custom ML models
└── docs/             # Documentation
```

### 4.2.2 Backend Architecture

The backend contains 10 Django application modules: core (base utilities), users (authentication), assessments (skill evaluation), roadmaps (learning paths), courses (aggregation), advisory (AI chatbot), jobs (market data), progress (tracking), career_tools (resume builder), and notifications.

Each module follows a consistent structure with models, serializers, views, services, and tests. The service layer pattern separates business logic from API views, improving testability.

### 4.2.3 Design Patterns

**Service Layer Pattern**: Business logic resides in dedicated service classes rather than views. All 10 modules implement this pattern through services.py files.

**Repository Pattern**: Django ORM managers act as repositories. A custom SoftDeleteManager filters out deleted records by default while providing access to all records when needed.

**Strategy Pattern**: The AI component supports multiple LLM providers through interchangeable strategy classes for model inference.

**Template Method Pattern**: The BaseModel class defines the soft delete algorithm, allowing subclasses to inherit consistent deletion behavior.

### 4.2.4 Frontend Architecture

The frontend organizes code into pages (route components), components (reusable UI), hooks (custom React hooks), and lib (utilities and API client). Type definitions ensure consistency between frontend and backend data structures.

---

## 4.3 Data Structures and Databases

### 4.3.1 Design Principles

The database follows these principles:
- Third Normal Form for data integrity
- UUID primary keys for distributed system readiness
- Soft deletes for data recovery capability
- Comprehensive indexing for query performance
- JSONB fields for flexible nested data

### 4.3.2 BaseModel Architecture

All application models inherit from a BaseModel class that combines three abstract mixins: UUIDModel (UUID primary key), TimeStampedModel (created_at/updated_at timestamps), and SoftDeleteModel (is_deleted flag with restore capability). This ensures consistent behavior across all 25+ database tables.

The dual manager pattern provides two query interfaces: the default manager returns only active records, while an alternate manager includes soft-deleted records for administrative purposes.

### 4.3.3 Schema Organization

**Table 4.4: Database Modules**

| Module | Key Tables | Purpose |
|--------|------------|---------|
| Users | users, skills, user_skills | Authentication and profiles |
| Assessments | assessments, assessment_results | Skill evaluation with JSONB responses |
| Roadmaps | roadmaps, phases, milestones | Learning path structure |
| Courses | courses, course_platforms | External course aggregation |
| Advisory | conversations, messages | AI chatbot with RAG context |
| Jobs | jobs, job_platforms, job_skills | Market data from scraping |

### 4.3.4 JSONB Usage

PostgreSQL JSONB fields store flexible data structures that vary between records. Assessment questions use JSONB to accommodate different question types (multiple choice, scale, text) without schema changes. Skill scores store nested category structures, and AI recommendations store variable-length arrays of career suggestions with match scores.

### 4.3.5 Indexing Strategy

The database implements indexes on: all foreign keys for join performance, frequently filtered columns (is_deleted, status, created_at), GIN indexes on JSONB columns for nested queries, and composite indexes for common query patterns like user-assessment lookups.

---

## 4.4 Quantitative Results

### 4.4.1 Performance Targets

**Table 4.5: Performance Requirements**

| Metric | Target | Status |
|--------|--------|--------|
| Non-AI API Response | ≤ 2 seconds | Not yet measured |
| AI API Response | ≤ 7 seconds | Not yet measured |
| Assessment Generation | < 30 seconds | Planned (Phase 6) |
| Roadmap Generation | < 60 seconds | Planned (Phase 6) |
| Concurrent Users | 300+ | Not yet tested |

### 4.4.2 Test Coverage

**Table 4.6: Current Test Status**

| Module | Tests | Status |
|--------|-------|--------|
| Users | 51 | Passing (Phase 1) |
| Assessments | 16 | Passing (Phase 2) |
| Roadmaps | TBD | Phase 3 |
| Jobs | TBD | Phase 4 |
| **Total** | **67** | **Passing** |

### 4.4.3 Codebase Metrics

| Component | Approximate Size |
|-----------|------------------|
| Backend (models, views, services) | ~5,000 lines |
| Frontend (components, pages) | ~5,000 lines |
| Database Schema | 25+ tables |
| Dependencies | 100+ packages total |

---

## 4.5 Qualitative Results

### 4.5.1 Code Quality Observations

**Consistency**: All models inherit from BaseModel, ensuring uniform UUID keys, timestamps, and soft delete across the system. The service layer pattern is consistently applied across all 10 modules.

**Type Safety**: TypeScript in the frontend catches errors at compile time and provides self-documenting interfaces for API responses.

**Separation of Concerns**: Views handle HTTP concerns while services contain business logic, making the codebase easier to test and maintain.

### 4.5.2 Architectural Decisions

**Modular Monolith**: Chosen over microservices for MVP simplicity. Provides ACID transactions across modules and direct Python imports without network overhead. Can migrate to microservices later if needed.

**Local LLM Approach**: Using 4-bit quantized models (Dettmers et al., 2023) eliminates API costs while maintaining acceptable quality. Models fit in ~5GB VRAM on consumer hardware.

**RAG for Advisory**: Retrieval-Augmented Generation (Lewis et al., 2020) grounds AI responses in domain-specific knowledge, reducing hallucination and enabling knowledge updates without retraining.

### 4.5.3 Areas for Improvement

- Add React error boundaries for graceful failure handling
- Implement Redis caching for frequently accessed data
- Add API rate limiting for public endpoints
- Expand test coverage to remaining modules

---

## References

Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). QLoRA: Efficient finetuning of quantized LLMs. *Advances in Neural Information Processing Systems, 36*.

Django Software Foundation. (2024). *Django documentation*. https://docs.djangoproject.com/

Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., & Chen, W. (2022). LoRA: Low-rank adaptation of large language models. *International Conference on Learning Representations*.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459-9474.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing*.

Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M. A., Lacroix, T., ... & Lample, G. (2023). LLaMA: Open and efficient foundation language models. *arXiv preprint arXiv:2302.13971*.

Touvron, H., Martin, L., Stone, K., Albert, P., Almahairi, A., Babaei, Y., ... & Scialom, T. (2023). Llama 2: Open foundation and fine-tuned chat models. *arXiv preprint arXiv:2307.09288*.

---
